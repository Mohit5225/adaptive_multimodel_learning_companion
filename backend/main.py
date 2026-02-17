#!/usr/bin/env python
"""
Main CLI Entry Point
Usage: python main.py "visualize 3+2 addition"
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Services.orchestrator import VideoOrchestrator


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Math Video Generator")
        print("=" * 60)
        print("\nUsage: python main.py \"<concept>\"")
        print("\nExamples:")
        print('  python main.py "visualize 3+2 addition"')
        print('  python main.py "explain vector addition"')
        print('  python main.py "show matrix transformation"')
        print('  python main.py "demonstrate fractions 1/2 + 1/4"')
        print("\nOutput: final_video.mp4 with Hinglish narration")
        return
    
    concept = sys.argv[1]
    
    print("=" * 60)
    print("🎬 MATH VIDEO GENERATOR")
    print("=" * 60)
    print(f"\n📝 Concept: {concept}")
    print(f"🎯 Goal: 180-220s narrated video (~3-4 minutes with 10 beats)")
    
    # Create orchestrator and generate video
    orchestrator = VideoOrchestrator(output_dir="output")
    result = orchestrator.generate_video(concept, verbose=True)
    
    # Final summary
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
