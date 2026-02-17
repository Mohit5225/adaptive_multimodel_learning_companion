#!/usr/bin/env python
"""
Cartesia Main CLI Entry Point
Usage: python cartesia_main.py "visualize 3+2 addition"
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Services.cartesia_orchestrator import CartesiaVideoOrchestrator


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Math Video Generator (CARTESIA TTS)")
        print("=" * 60)
        print("\nUsage: python cartesia_main.py \"<concept>\"")
        print("\nExamples:")
        print('  python cartesia_main.py "visualize 3+2 addition"')
        print('  python cartesia_main.py "explain vector addition"')
        print('  python cartesia_main.py "show matrix transformation"')
        print('  python cartesia_main.py "demonstrate fractions 1/2 + 1/4"')
        print("\nOutput: final_video_cartesia.mp4 with Cartesia TTS narration")
        print("\nNote: For Google TTS, use main.py instead")
        return
    
    concept = sys.argv[1]
    
    print("=" * 60)
    print("🎬 MATH VIDEO GENERATOR (CARTESIA TTS)")
    print("=" * 60)
    print(f"\n📝 Concept: {concept}")
    print(f"🎯 Goal: 180-220s narrated video (~3-4 minutes with 10 beats)")
    print(f"🔊 TTS Engine: Cartesia (word-level timestamps)")
    
    # Create orchestrator and generate video
    orchestrator = CartesiaVideoOrchestrator(output_dir="output")
    result = orchestrator.generate_video(concept, verbose=True)
    
    # Final summary
    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"📹 Final Video: {result['final_video_path']}")
        print(f"🔊 Audio: {result['audio_path']}")
        print(f"📄 Manim Code: {result['manim_code_path']}")
        print(f"📝 Narration: {result.get('narration_path', 'N/A')}")
    else:
        print("❌ FAILED")
        print("=" * 60)
        print(f"Error: {result['error']}")
        if result.get('manim_code_path'):
            print(f"Check Manim code at: {result['manim_code_path']}")


if __name__ == "__main__":
    main()
