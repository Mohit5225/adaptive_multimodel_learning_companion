"""
Gemini Chat Service: Classifier + Contextual Text Response Generator
Two Gemini API calls:
  1. classify_message() — Routes user input to VIDEO or TEXT pipeline
  2. generate_text_response() — Produces context-aware reply using last 20 messages
"""
import json
import os
import re
from typing import List, Dict, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompts.modes import get_mode_prompt, DEFAULT_MODE

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ═════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═════════════════════════════════════════════════════════════════════════════

CLASSIFIER_SYSTEM_PROMPT = """
You are the Learning System's Intelligent Router. Your ONLY job is to classify the user's request into ONE of three strict routing pipelines based on explicit keywords and intent.

1. CLASSIFY every incoming user message into `need_video_visualisation`, `need_text_response`, or `need_rag_search`.
2. OUTPUT strictly in JSON format.

--- CLASSIFICATION CATEGORIES

need_video_visualisation — Explicit requests for visual content.
- Triggers: "video", "visualize", "show me", "animation", "diagram", "watch", "animate", "render", "draw".
- Logic: If ANY of these words appear, route here.

need_rag_search — Questions about uploaded PDF documents or student notes.
- Triggers: "my notes", "in the PDF", "according to", "from the document", "in the material", "the file says", "check my", "reference", "from my notes", "what does my", "my document".
- Logic: If user is asking to search or find information in their uploaded materials, route here.

need_text_response — All other queries (The Default).
- Triggers: Questions, explanations, code, math, chatting, definitions, general knowledge.
- Logic: If it does not explicitly ask to SEE something or search uploaded materials, it goes here.

--- CRITICAL ROUTING RULES

**The "Keyword" Check:**
- "Explain gravity" = TEXT (general explanation)
- "Show me gravity" = VIDEO (wants visual animation)
- "What does my PDF say about gravity?" = RAG (search uploaded materials)
- Do not infer. Do not guess. Default to TEXT if unsure.

--- OUTPUT FORMAT (JSON Only)

Always respond with JSON only, nothing else:

{
  "category": "need_video_visualisation" or "need_text_response" or "need_rag_search",
  "reason": "Found keyword [INSERT KEYWORD] OR No visual/RAG keywords found (Default)"
}
"""

TEXT_RESPONSE_SYSTEM_PROMPT = """
You are Socratic AI — an adaptive, personalised educational chatbot for Indian students (ages 12-22).

YOUR PERSONALITY:
- Warm, encouraging, and patient like a favourite tutor
- You explain with analogies, real-world examples, and step-by-step breakdowns
- You ask follow-up questions to check understanding (Socratic method)
- You adapt complexity based on the student's previous messages

YOUR RULES:
1. Keep responses concise but thorough (150-400 words max)
2. Use markdown formatting for clarity (bold, lists, code blocks for math)
3. If the student is struggling (based on chat history), simplify your language
4. If the student is advanced (based on chat history), increase depth
5. Always end with an engaging question or next step suggestion
6. For math, use clear notation and step-by-step solutions
7. Be encouraging — celebrate when they get things right
8. If you don't know something, say so honestly

CONTEXT AWARENESS:
- You will receive the last 20 messages of conversation history
- Use this to maintain continuity, avoid repetition, and personalise responses
- Reference previous topics when relevant ("As we discussed earlier about vectors...")
- Track what the student knows and doesn't know
"""

RAG_GROUNDING_PROMPT = """

REFERENCE MATERIAL (PDF CONTEXT):
You have access to relevant excerpts from the student's uploaded PDF document(s).
Use this information to ground your answers — always prefer PDF content over general knowledge
when the student's question relates to the uploaded material.

CRITICAL RAG RULES:
1. If the student asks about something covered in the PDF excerpts below, BASE your answer on that content.
2. You may supplement with your own knowledge to explain concepts more clearly, but never contradict the PDF.
3. When referencing PDF content, say things like "According to your material..." or "As mentioned in your notes..."
4. If the question is unrelated to the PDF content, answer normally using your general knowledge.
5. Do NOT mention "chunks", "vectors", "embeddings", or any technical RAG terminology to the student.

--- RELEVANT PDF EXCERPTS ---
{rag_context}
--- END OF PDF EXCERPTS ---
"""


class GeminiChatService:
    """
    Handles all Gemini API interactions for the chatbot:
    - Message classification (VIDEO vs TEXT routing)
    - Context-aware text response generation
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=self.api_key)

    # ─────────────────────────────────────────────────────────────────────
    # 1. CLASSIFIER — First Gemini API Call
    # ─────────────────────────────────────────────────────────────────────
    def classify_message(self, user_message: str) -> Dict:
        """
        Classify a user message into 'need_video_visualisation', 'need_text_response', or 'need_rag_search'.
        Returns: {"category": str, "reason": str, "confidence": float}
        """
        print(f"\n🔀 [Classifier] Starting classification for message: '{user_message[:80]}...'")
        print(f"   🔀 [Classifier] Using model: gemini-2.0-flash")
        print(f"   🔀 [Classifier] System prompt length: {len(CLASSIFIER_SYSTEM_PROMPT)} chars")

        try:
            print(f"   🔀 [Classifier] Calling Gemini API...")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=CLASSIFIER_SYSTEM_PROMPT,
                    temperature=0.1,  # Low temperature for deterministic classification
                    max_output_tokens=200,
                ),
            )

            raw_text = response.text.strip()
            print(f"   🔀 [Classifier] Raw Gemini response: {raw_text}")

            # Parse JSON from response (handle markdown code blocks)
            json_str = raw_text
            if "```" in json_str:
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', json_str, re.DOTALL)
                json_str = json_match.group(1) if json_match else raw_text
                print(f"   🔀 [Classifier] Extracted JSON from code block: {json_str}")

            result = json.loads(json_str)
            print(f"   🔀 [Classifier] Parsed JSON: {result}")

            # Validate and normalize
            category = result.get("category", "need_text_response")
            valid_categories = ["need_video_visualisation", "need_text_response", "need_rag_search"]
            if category not in valid_categories:
                print(f"   ⚠️ [Classifier] Invalid category '{category}', defaulting to 'need_text_response'")
                category = "need_text_response"

            classification = {
                "category": category,
                "reason": result.get("reason", "Classified by Gemini"),
                "confidence": 1.0,
            }

            print(f"   ✅ [Classifier] Final result: {classification['category']} — {classification['reason']}")
            return classification

        except json.JSONDecodeError as e:
            print(f"   ❌ [Classifier] JSON parsing error: {e}. Raw text: {raw_text}")
            return {
                "category": "need_text_response",
                "reason": f"JSON parsing error (defaulted to text): {str(e)}",
                "confidence": 0.5,
            }
        except Exception as e:
            print(f"   ❌ [Classifier] Unexpected error: {e}. Defaulting to text_response.")
            return {
                "category": "need_text_response",
                "reason": f"Classification error (defaulted to text): {str(e)}",
                "confidence": 0.5,
            }

    # ─────────────────────────────────────────────────────────────────────
    # 2. TEXT RESPONSE — Second Gemini API Call (with context)
    # ─────────────────────────────────────────────────────────────────────
    def generate_text_response(
        self,
        user_message: str,
        chat_history: List[Dict] = None,
        mode: str = None,
        rag_context: str = None,
    ) -> str:
        """
        Generate a context-aware text response using Gemini.
        Includes last 20 messages as conversation history for personalisation.
        Dynamically appends mode-specific personality overlay.
        Optionally injects RAG context from uploaded PDFs.

        Args:
            user_message: The current user message
            chat_history: List of previous messages [{role, content}, ...]
            mode: Teaching mode key (socratic, quiz, casual, eli5, exam_prep)
            rag_context: Optional formatted context from PDF RAG search

        Returns:
            str: The AI's text response
        """
        active_mode = mode or DEFAULT_MODE
        print(f"\n💬 [TextGen] Starting text response generation for: '{user_message[:80]}...'")
        print(f"   💬 [TextGen] Using model: gemini-2.0-flash")
        print(f"   💬 [TextGen] Active mode: {active_mode}")
        print(f"   💬 [TextGen] Chat history length: {len(chat_history) if chat_history else 0} messages")
        print(f"   💬 [TextGen] RAG context: {'YES (' + str(len(rag_context)) + ' chars)' if rag_context else 'NO (no PDF in this chat)'}")

        # Build system prompt: base + mode overlay + optional RAG grounding
        mode_overlay = get_mode_prompt(active_mode)
        system_prompt = TEXT_RESPONSE_SYSTEM_PROMPT + "\n\n" + mode_overlay

        # Inject RAG context if available (PDF is attached to this chat)
        if rag_context:
            system_prompt += RAG_GROUNDING_PROMPT.format(rag_context=rag_context)
            print(f"   📄 [TextGen] RAG grounding injected into system prompt")

        print(f"   💬 [TextGen] System prompt length: {len(system_prompt)} chars (base + {active_mode} mode{' + RAG' if rag_context else ''})")

        try:
            # Build conversation contents for Gemini
            contents = self._build_conversation_contents(user_message, chat_history)
            print(f"   💬 [TextGen] Built conversation contents ({len(contents)} parts)")

            print(f"   💬 [TextGen] Calling Gemini API...")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,  # Creative but focused
                    max_output_tokens=1024,
                ),
            )

            ai_response = response.text.strip()
            print(f"   ✅ [TextGen] Response generated successfully ({len(ai_response)} chars)")
            print(f"   📝 [TextGen] Response preview: {ai_response[:100]}...")
            return ai_response

        except Exception as e:
            print(f"   ❌ [TextGen] Error generating response: {e}")
            return f"I'm sorry, I encountered an error processing your request. Could you try rephrasing? (Error: {str(e)})"

    # ─────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────
    def _build_conversation_contents(
        self,
        current_message: str,
        chat_history: List[Dict] = None,
    ) -> list:
        """
        Build Gemini-compatible conversation contents from chat history.
        Maps our chat history format to Gemini's expected Content format.
        """
        contents = []

        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=content)],
                        )
                    )
                elif role == "ai":
                    contents.append(
                        types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=content)],
                        )
                    )

        # Add current message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=current_message)],
            )
        )

        print(f"   📚 [Context] Built conversation with {len(contents)} messages ({len(chat_history or [])} history + 1 current)")
        return contents
