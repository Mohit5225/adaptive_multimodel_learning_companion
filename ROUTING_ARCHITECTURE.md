# System Architecture: 3-Way Message Router

```
USER MESSAGE INPUT
        ↓
  "Explain gravity"
  "Show me gravity"
  "What's in my PDF about gravity?"
        ↓
═════════════════════════════════════════════════════════════════════════════
           INTELLIGENT CLASSIFIER (Gemini 2.0 Flash)
═════════════════════════════════════════════════════════════════════════════
        ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Analyzes message for keywords:                                         │
│  ✓ Visual keywords: "show", "visualize", "animate", "diagram"          │
│  ✓ PDF keywords: "my PDF", "my notes", "according to", "document"      │
│  ✓ Default: Regular text response                                       │
└─────────────────────────────────────────────────────────────────────────┘
        ↓
        ├──────────────────────────┬──────────────────────────┬──────────────────────────┐
        ↓                          ↓                          ↓
   CATEGORY 1              CATEGORY 2                   CATEGORY 3
 need_video_            need_text_              need_rag_search
visualisation           response                   (NEW!)
        │                       │                          │
        │                       │                          │
        ↓                       ↓                          ↓
   ┌─────────────┐        ┌──────────────┐         ┌───────────────┐
   │  🎬 VIDEO   │        │  💬 TEXT     │         │  📄 RAG/PDF   │
   │ PIPELINE    │        │  PIPELINE    │         │  PIPELINE     │
   └─────────────┘        └──────────────┘         └───────────────┘
        │                       │                          │
        │                       │                          │
        ↓                       ↓                          ↓
   1. Check PDFs          1. Get chat              1. Check: Are
      exist?                 history                  PDFs uploaded?
   2. Create                   (last 20)                  │
      project                  │                         ├─ YES
   3. Start                    ↓                         │   → Query Qdrant
      Cartesia            2. Check: PDFs?                │     Vector DB
      generation            │                           │
      (async)               ├─ YES                       ├─ Remember RAG
                            │  → Search                  │   context
   Return:                  │    Qdrant                   │
   "Video                    │    (hybrid)            2. Generate
    generating"              │                           response
   (project_id)              ├─ NO                       with RAG
                             │  → Skip RAG              grounding
                             │                       3. Save to DB
                             ↓                      4. Return
                        3. Generate                   response
                           response
                           using:
                           - Last 20 msgs
                           - Teaching mode
                           - ±RAG context
                        4. Save to DB
                        5. Return
                           response
```

## Decision Points

### 🔀 Classifier Decision Tree

```
User Message
    ↓
Has visual keywords?
  (show, visualize, animate, draw, diagram, watch, render, video)
    ├─ YES → VIDEO GENERATION
    │         (Create cartesia project, generate manim video)
    │
    └─ NO
        ↓
    Has PDF keywords?
      (my PDF, my notes, document, according to, reference, material)
        ├─ YES → RAG SEARCH
        │         (Search Qdrant + generate with context)
        │
        └─ NO
            ↓
          TEXT RESPONSE (DEFAULT)
          (Answer normally, optional RAG if PDFs exist)
```

## Message Flow Comparison

### BEFORE (2-Category System)
```
User: "What's in my PDF about gravity?"
        ↓
  Classifier (limited)
        ├─ Video? NO
        └─ → TEXT (default)
        ↓
  RAG search happens by chance
  (not guaranteed)
        ↓
  Result: Works sometimes, fails others
```

### AFTER (3-Category System)
```
User: "What's in my PDF about gravity?"
        ↓
  Classifier (enhanced)
        ├─ Video? NO
        ├─ PDF keywords? YES
        └─ → RAG SEARCH (guaranteed!)
        ↓
  Always checks for PDFs
        ├─ Found? → Search & ground response
        └─ Not found? → User-friendly message
        ↓
  Result: Consistent, predictable behavior
```

## Routing Matrix

| User Says | Category | Pipeline | RAG Used |
|-----------|----------|----------|----------|
| "Show me gravity" | VIDEO | Video Generation | ❌ |
| "Explain gravity" | TEXT | Text Response | ⚠️ Optional |
| "Show gravity animation" | VIDEO | Video Generation | ❌ |
| "What's gravity?" | TEXT | Text Response | ⚠️ Optional |
| "What does my PDF say about gravity?" | **RAG** | **RAG Search** | ✅ Required |
| "According to my notes, what is gravity?" | **RAG** | **RAG Search** | ✅ Required |
| "From the document, explain gravity" | **RAG** | **RAG Search** | ✅ Required |
| "My material covers gravity, right?" | **RAG** | **RAG Search** | ✅ Required |

## Example Execution Traces

### Example 1: RAG Request
```
USER INPUT
  Message: "What does my PDF say about photosynthesis?"
        ↓
CLASSIFIER
  Keywords found: ["PDF", "my"]
  Category: need_rag_search ✅
        ↓
CHAT ROUTER (RAG Pipeline)
  Check PDFs for chat_id
    Found: 2 PDFs
  Search Qdrant
    Query: "What does my PDF say about photosynthesis?"
    Found: 3 relevant chunks (95%, 87%, 82% similarity)
  Generate response
    PROMPT: "Here are PDF excerpts: [chunk1] [chunk2] [chunk3]"
    Response: "According to your PDF, photosynthesis is..."
  Save to MongoDB
    routed_to: "rag_search"
    system_response: "According to your PDF..."
        ↓
USER RECEIVES
  Answer grounded in their uploaded PDF ✅
```

### Example 2: Video Request with PDFs
```
USER INPUT
  Message: "Show me how photosynthesis works with an animation"
        ↓
CLASSIFIER
  Keywords found: ["Show", "animation"]
  Category: need_video_visualisation ✅
        ↓
CHAT ROUTER (Video Pipeline)
  ⚠️ Note: RAG is SKIPPED for video
  Create Cartesia project
  Start Manim generation (async)
  Return: "🎬 Generating your visualization..."
        ↓
USER RECEIVES
  Video generation started (PDFs not used for video)
```

### Example 3: Text with Optional RAG
```
USER INPUT
  Message: "Explain how photosynthesis works"
        ↓
CLASSIFIER
  Keywords found: [] (no visual, no PDF keywords)
  Category: need_text_response ✅
        ↓
CHAT ROUTER (Text Pipeline)
  Check: Does chat have PDFs?
    YES → Optional RAG search
    Result: "Photosynthesis is a process where... [based on PDF if relevant]"
    OR
    NO → Regular response
    Result: "Photosynthesis is the process where plants..."
        ↓
USER RECEIVES
  Answer (enhanced by PDF if available)
```

## Logging Output Examples

### When Classifier Routes to RAG
```
🔀 [Classifier] Starting classification for message: 'What does my PDF say about photosynthesis?'
   🔀 [Classifier] Using model: gemini-2.0-flash
   🔀 [Classifier] System prompt length: 1850 chars
   🔀 [Classifier] Calling Gemini API...
   🔀 [Classifier] Raw Gemini response: {"category": "need_rag_search", "reason": "Found keyword 'PDF'"}
   🔀 [Classifier] Parsed JSON: {'category': 'need_rag_search', 'reason': 'Found keyword "PDF"'}
   ✅ [Classifier] Final result: need_rag_search — Found keyword "PDF"
📄 [Chat] Routing to RAG SEARCH pipeline — searching uploaded PDFs...
📄 [Chat] Chat has 2 PDF(s) — performing RAG search...
✅ [Chat] RAG context retrieved (1450 chars)
🤖 [Chat] Generating response with RAG grounding...
✅ [Chat] Text response generated (320 chars)
💾 [Chat] Message saved to database (id: msg_abc123)
🎉 [Chat] RAG search completed successfully
```

### When Classifier Detects No PDFs Mentioned
```
🔀 [Classifier] Starting classification for message: 'Explain photosynthesis'
   🔀 [Classifier] Calling Gemini API...
   🔀 [Classifier] Raw Gemini response: {"category": "need_text_response", "reason": "No visual/RAG keywords found (Default)"}
   ✅ [Classifier] Final result: need_text_response — No visual/RAG keywords found
💬 [Chat] Routing to TEXT pipeline — generating response...
📚 [Chat] Retrieved 3 messages for context
📄 [Chat] Chat has 2 PDF(s) — performing optional RAG search...
✅ [Chat] RAG context retrieved (800 chars)
🤖 [Chat] Calling Gemini for text response (mode: socratic, RAG: YES)...
✅ [Chat] Text response generated (285 chars)
💾 [Chat] Message saved to database (id: msg_def456)
🎉 [Chat] Text response sent successfully
```

---

This ensures that **PDF-related questions always use RAG**, while maintaining backward compatibility with video and text requests.
