"""
Cartesia Orchestrator: Main workflow controller for Cartesia TTS
Ties all 5 steps together: Lesson Plan → Cartesia TTS → Manim → Render → Overlay
"""
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Import services
from .lesson_plan import GeminiService, LessonPlan
from .video_service import overlay_audio_on_video, get_audio_duration
from cartesia_tts_service.audio_generation import AudioGenerationService  # CARTESIA
from cartesia_tts_service.timestamp_extraction import create_plain_transcript, map_cartesia_timestamps_to_beats  # CARTESIA
from utils.filename_generator import generate_video_filename


# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class CartesiaVideoOrchestrator:
    """
    Orchestrates the full video generation pipeline with Cartesia TTS:
    1. Generate lesson plan from concept
    2. Generate Cartesia TTS audio with word-level timestamps
    3. Generate timestamp-aware Manim code
    4. Render Manim video
    5. Overlay audio on video
    """
    
    def __init__(self, output_dir: str = "output", chat_id: str = None, message_id: str = None):
        self.output_dir = output_dir
        self.chat_id = chat_id
        self.message_id = message_id
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize services
        self.lesson_service = GeminiService(api_key=GEMINI_API_KEY)
        self.tts_service = AudioGenerationService()  # Cartesia TTS
    
    def _extract_language(self, concept: str) -> str:
        """Extract language from concept string. Defaults to hinglish."""
        print(f"\n🔍 LANGUAGE DETECTION:")
        print(f"   📝 Input concept: {concept}")
        
        concept_lower = concept.lower()
        print(f"   📝 Lowercase concept: {concept_lower}")
        
        # First, check for explicit language keywords
        # Check for Gujarati keywords
        gujarati_keywords = ["in gujarati", "gujarati ma", "ગુજરાતી", "ગુજરાતીમાં"]
        gujarati_keyword_matches = [pattern for pattern in gujarati_keywords if pattern in concept_lower]
        if gujarati_keyword_matches:
            print(f"   ✅ GUJARATI detected via keywords - matches: {gujarati_keyword_matches}")
            return "gujarati"
        
        # Check for Hindi keywords
        hindi_keywords = ["in hindi", "hindi mein", "हिंदी", "हिंदी में"]
        hindi_keyword_matches = [pattern for pattern in hindi_keywords if pattern in concept_lower]
        if hindi_keyword_matches:
            print(f"   ✅ HINDI detected via keywords - matches: {hindi_keyword_matches}")
            return "hindi"
        
        # Check for Marathi keywords
        marathi_keywords = ["in marathi", "marathi madhe", "मराठी", "मराठी मध्ये"]
        marathi_keyword_matches = [pattern for pattern in marathi_keywords if pattern in concept_lower]
        if marathi_keyword_matches:
            print(f"   ✅ MARATHI detected via keywords - matches: {marathi_keyword_matches}")
            return "marathi"
        
        # Check for English keywords
        english_keywords = ["in english", "pure english"]
        english_keyword_matches = [pattern for pattern in english_keywords if pattern in concept_lower]
        if english_keyword_matches:
            print(f"   ✅ ENGLISH detected via keywords - matches: {english_keyword_matches}")
            return "english"
        
        # Second, detect language based on script/characters used in the text
        print(f"   🔍 No explicit keywords found. Analyzing script characters...")
        
        # Count characters from different scripts
        gujarati_chars = sum(1 for char in concept if '\u0A80' <= char <= '\u0AFF')  # Gujarati Unicode block
        devanagari_chars = sum(1 for char in concept if '\u0900' <= char <= '\u097F')  # Devanagari (Hindi/Marathi)
        latin_chars = sum(1 for char in concept if 'a' <= char.lower() <= 'z')
        
        total_chars = len([c for c in concept if c.isalpha()])
        
        print(f"   📊 Character analysis:")
        print(f"      - Gujarati chars: {gujarati_chars}")
        print(f"      - Devanagari chars: {devanagari_chars}")
        print(f"      - Latin chars: {latin_chars}")
        print(f"      - Total alphabetic chars: {total_chars}")
        
        if total_chars > 0:
            gujarati_ratio = gujarati_chars / total_chars
            devanagari_ratio = devanagari_chars / total_chars
            latin_ratio = latin_chars / total_chars
            
            print(f"   📊 Script ratios:")
            print(f"      - Gujarati: {gujarati_ratio:.2f}")
            print(f"      - Devanagari: {devanagari_ratio:.2f}")
            print(f"      - Latin: {latin_ratio:.2f}")
            
            # If majority (>50%) is in a specific script, detect that language
            if gujarati_ratio > 0.5:
                print(f"   ✅ GUJARATI detected via script analysis ({gujarati_ratio:.1%} Gujarati chars)")
                return "gujarati"
            elif devanagari_ratio > 0.5:
                # Need to distinguish between Hindi and Marathi (both use Devanagari)
                # For now, we'll assume Hindi as it's more common
                print(f"   ✅ HINDI detected via script analysis ({devanagari_ratio:.1%} Devanagari chars)")
                return "hindi"
            elif latin_ratio > 0.8:  # High threshold for pure English
                print(f"   ✅ ENGLISH detected via script analysis ({latin_ratio:.1%} Latin chars)")
                return "english"
        
        print(f"   ⚠️ NO SPECIFIC LANGUAGE detected - defaulting to HINGLISH")
        return "hinglish"  # default
    
    def _get_cartesia_voice(self, language: str) -> dict:
        """
        Select appropriate Cartesia voice based on language.
        
        NOTE: Cartesia has limited multilingual support. Using English voice for now.
        Supported languages with timestamps: English, German, Spanish, French
        """
        print(f"🔊 Selecting Cartesia voice for language: {language}")
        
        # Cartesia voice IDs (using English-speaking voices for now)
        # You can find more voices at: https://cartesia.ai/voices
        voice_map = {
            "gujarati": {
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Aoede (warm female)
            },
            "hindi": {
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Aoede (warm female)
            },
            "marathi": {
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Aoede (warm female)
            },
            "english": {
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Aoede (warm female)
            },
            "hinglish": {  # Default fallback
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Aoede (warm female)
            }
        }
        
        selected_voice = voice_map.get(language, voice_map["hinglish"])
        print(f"   ✅ Selected Cartesia voice ID: {selected_voice['id']}")
        print(f"   ⚠️  Note: Using English voice for all languages (Cartesia limitation)")
        return selected_voice
    
    def generate_video(self, prompt: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Full pipeline: prompt → final video with Cartesia narration.
        Generates human-readable filename based on prompt content.
        
        Args:
            prompt: User's original prompt (becomes concept for lesson planning & filename)
            verbose: Print progress updates
        
        Returns:
            Dict with paths, status info, and human-readable video filename
        """
        # Use prompt as the concept for lesson planning
        concept = prompt
        
        if verbose:
            print("\n" + "⚡"*30)
            print("🎬 INITIALIZING CARTESIA ORCHESTRATOR PIPELINE")
            print(f"🎬 Prompt: {prompt}")
            print("⚡"*30)

        result = {
            "success": False,
            "concept": concept,
            "original_prompt": prompt,
            "language": None,
            "lesson_plan": None,
            "audio_path": None,
            "timestamps": None,
            "manim_code_path": None,
            "video_path": None,
            "final_video_path": None,
            "video_filename": None,
            "error": None
        }
        
        try:
            # ═══════════════════════════════════════════════════════════════════
            # STEP 0: Extract Language from Concept
            # ═══════════════════════════════════════════════════════════════════
            language = self._extract_language(concept)
            result["language"] = language
            
            if verbose:
                print("\n" + "=" * 60)
                print(f"🎯 FINAL Language detected: {language.upper()}")
                print(f"🔄 This will be passed to GeminiService.generate_lesson_plan()")
                print("=" * 60)
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 1: Generate Lesson Plan
            # ═══════════════════════════════════════════════════════════════════
            if verbose:
                print("\n" + "=" * 60)
                print(f"STEP 1: Generating {language.upper()} Lesson Plan...")
                print(f"📞 Calling: lesson_service.generate_lesson_plan(concept='{concept}', language='{language}')")
                print("=" * 60)
            
            lesson_plan = self.lesson_service.generate_lesson_plan(
                concept=concept,
                language=language
            )
            
            if verbose:
                print(f"📋 Generated lesson plan with {len(lesson_plan.beats)} beats")
                print(f"📋 Title: {lesson_plan.title}")
                print(f"📋 Sample narration from beat1: {lesson_plan.beats[0].narration_text[:100] if lesson_plan.beats else 'No beats'}...")
            result["lesson_plan"] = lesson_plan.model_dump()
            
            # Save narration to a separate file
            narration_path = os.path.join(self.output_dir, "narration.txt")
            with open(narration_path, "w", encoding="utf-8") as f:
                f.write(f"Title: {lesson_plan.title}\n")
                f.write(f"Language: {language}\n")
                f.write(f"TTS Engine: Cartesia\n\n")
                for beat in lesson_plan.beats:
                    clean_narration = beat.narration_text
                    f.write(f"{beat.beat_id}: {clean_narration}\n\n")
            result["narration_path"] = narration_path
            
            if verbose:
                print(f"✅ Narration saved: {narration_path}")
                print(f"✅ Title: {lesson_plan.title}")
                print(f"✅ Beats: {len(lesson_plan.beats)}")
                print(f"✅ Est. Duration: {lesson_plan.total_duration_estimate}s")
                for beat in lesson_plan.beats:
                    clean_narration = beat.narration_text
                    print(f"   - {beat.beat_id}: {clean_narration[:50]}...")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 2: Generate Cartesia TTS Audio + Word-Level Timestamps
            # ═══════════════════════════════════════════════════════════════════
            if verbose:
                print("\n" + "=" * 60)
                print("STEP 2: Generating Cartesia TTS Audio...")
                print("=" * 60)
            
            # Convert beats to plain transcript (Cartesia doesn't need SSML)
            beats_data = [b.model_dump() for b in lesson_plan.beats]
            # Sanitize all narration to remove control characters
            for beat in beats_data:
                beat['narration_text'] = beat['narration_text']
            
            # Create plain transcript from beats
            transcript = create_plain_transcript(beats_data)
            
            if verbose:
                print(f"📝 Transcript Preview:\n{transcript[:200]}...")
            
            # Select Cartesia voice based on detected language
            cartesia_voice = self._get_cartesia_voice(language)
            
            if verbose:
                print(f"🔊 Selected Cartesia voice ID: {cartesia_voice['id']}")
            
            # Generate audio with word-level timestamps
            audio_path, timepoints = self.tts_service.generate_audio(
                transcript=transcript,
                output_dir=self.output_dir,
                voice_params=cartesia_voice,
                audio_config_params={
                    "container": "mp3",
                    "sample_rate": 22050,
                    "encoding": "pcm_s16le",
                    "speed": 0.9  # Slightly slower for clarity
                },
                use_timestamps=True
            )
            
            result["audio_path"] = audio_path
            result["timestamps"] = timepoints
            
            # Map word-level timestamps to beats using Cartesia-specific mapping
            expected_beats = [b.beat_id for b in lesson_plan.beats]
            beat_timings = map_cartesia_timestamps_to_beats(timepoints, expected_beats)
            
            audio_duration = get_audio_duration(audio_path)
            
            if verbose:
                print(f"✅ Audio saved: {audio_path}")
                print(f"✅ Audio duration: {audio_duration:.1f}s")
                print(f"✅ Word-level timepoints: {len(timepoints)} words")
                print(f"✅ Beat timings: {beat_timings}")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 3: Generate Manim Code (The Architect's Brain)
            # ═══════════════════════════════════════════════════════════════════
            if verbose:
                print("\n" + "=" * 60)
                print("STEP 3: Generating Timestamp-Aware Manim Code...")
                print(f"🧠 [A.I.] Calling Gemini to translate lesson plan into Manim visuals")
                print("=" * 60)
            
            # Import here to avoid circular imports
            from Services.cli_gemini_manim import generate_manim_code_with_timestamps, render_manim_code
            
            manim_code, generation_status = generate_manim_code_with_timestamps(
                lesson_plan=lesson_plan,
                beat_timings=beat_timings,
                total_audio_duration=audio_duration,
                output_dir=self.output_dir
            )
            
            # Overwrite the file with the clean code to be 100% sure
            code_path = generation_status["saved_path"]
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(manim_code)
            
            result["manim_code_path"] = code_path
            result["generation_status"] = generation_status
            
            if verbose:
                if generation_status["success"]:
                    print(f"✅ Manim code PASSED on attempt {generation_status['attempt']}")
                else:
                    print(f"⚠️ Manim code FAILED after {generation_status['attempt']} attempts")
                print(f"✅ Code saved: {generation_status['saved_path']}")
                print(f"✅ Code length: {len(manim_code)} chars")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 4: Final Manim Render (Turning code into motion)
            # ═══════════════════════════════════════════════════════════════════
            if verbose:
                print("\n" + "=" * 60)
                print("STEP 4: Final Video Render (Executing Manim Engine)...")
                print("=" * 60)
            
            # OPTIMIZATION: If generation_status already returned a valid video path (from the trial render),
            # we can skip re-rendering if we trust it, OR we just use the path it gave us.
            # But render_manim_code in validation is usually low quality. We might want high quality here.
            # For now, let's keep it safe: re-render to ensure we have the file.
            
            if "video_path" in generation_status and generation_status["video_path"]:
                 # We have a path from validation!
                 video_path = generation_status["video_path"]
                 render_error = None
                 if not os.path.exists(video_path):
                     print("⚠️ Validated video file missing, re-rendering...")
                     video_path, render_error = render_manim_code(manim_code, "GeneratedScene")
            else:
                 video_path, render_error = render_manim_code(manim_code, "GeneratedScene")
            
            if render_error:
                result["error"] = f"Manim render failed: {render_error}"
                if verbose:
                    print(f"❌ Render error: {render_error[:200]}...")
                return result

            # Double check existence
            if not video_path:
                 result["error"] = "Render reported success but returned empty video path"
                 return result

            result["video_path"] = str(video_path) # Ensure it's a string
            
            if verbose:
                print(f"✅ Video rendered: {video_path}")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 5: Creative Fusion (Overlay Audio on Video)
            # ═══════════════════════════════════════════════════════════════════
            if verbose:
                print("\n" + "=" * 60)
                print("STEP 5: Final Fusion - Overlaying Audio on Video...")
                print(f"   🔊 Source Audio: {result['audio_path']}")
                print(f"   🎬 Source Video: {result['video_path']}")
                print("=" * 60)
            
            # Generate human-readable filename based on prompt content
            video_filename = generate_video_filename(
                prompt=prompt,
                chat_id=self.chat_id,
                message_id=self.message_id
            )
            final_video_path = os.path.join(self.output_dir, video_filename)
            
            if verbose:
                print(f"   📝 Generated filename: {video_filename}")
            
            success, overlay_result = overlay_audio_on_video(
                video_path=video_path,
                audio_path=audio_path,
                output_path=final_video_path
            )
            
            if not success:
                result["error"] = f"Audio overlay failed: {overlay_result}"
                if verbose:
                    print(f"❌ Overlay error: {overlay_result}")
                return result
            
            result["final_video_path"] = overlay_result
            result["video_filename"] = video_filename
            result["success"] = True
            
            if verbose:
                print(f"✅ Final video: {overlay_result}")
                print("\n" + "=" * 60)
                print("🎉 VIDEO GENERATION COMPLETE (Cartesia TTS)!")
                print("=" * 60)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            if verbose:
                print(f"\n❌ Pipeline error: {e}")
                import traceback
                traceback.print_exc()
            return result


def main():
    """CLI for Cartesia orchestrator testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate math video with Cartesia TTS")
    parser.add_argument("concept", type=str, help="Math concept to visualize")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 MATH VIDEO GENERATOR (CARTESIA TTS)")
    print("=" * 60)
    print(f"\n📝 Concept: {args.concept}")
    print(f"🎯 Goal: 180-220s narrated video with Cartesia voice")
    
    orchestrator = CartesiaVideoOrchestrator(output_dir=args.output)
    result = orchestrator.generate_video(args.concept)
    
    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"📹 Final Video: {result['final_video_path']}")
        print(f"🔊 Audio: {result['audio_path']}")
        print(f"📄 Manim Code: {result['manim_code_path']}")
    else:
        print("❌ FAILED")
        print("=" * 60)
        print(f"Error: {result['error']}")
        if result.get('manim_code_path'):
            print(f"Check Manim code at: {result['manim_code_path']}")


if __name__ == "__main__":
    main()
