"""
Video Service: FFmpeg audio-video overlay
Combines Manim-rendered video with TTS audio
"""
import os
import subprocess
from typing import Tuple


def overlay_audio_on_video(
    video_path: str,
    audio_path: str,
    output_path: str = None
) -> Tuple[bool, str]:
    """
    Overlay audio on video using FFmpeg.
    
    Args:
        video_path: Path to input video (from Manim)
        audio_path: Path to audio file (from TTS)
        output_path: Path for output video (optional, auto-generated if None)
    
    Returns:
        (success: bool, result_path_or_error: str)
    """
    if not os.path.exists(video_path):
        return False, f"Video file not found: {video_path}"
    
    if not os.path.exists(audio_path):
        return False, f"Audio file not found: {audio_path}"
    
    # Verify audio file has content
    audio_size = os.path.getsize(audio_path)
    if audio_size < 1000:  # Less than 1KB is suspicious
        return False, f"Audio file appears empty or corrupt: {audio_size} bytes"
    
    # Generate output path if not provided
    if output_path is None:
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_name}_final.mp4")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Get durations to determine strategy
    video_duration = get_video_duration(video_path)
    audio_duration = get_audio_duration(audio_path)
    
    print(f"📹 Video duration: {video_duration:.2f}s")
    print(f"🔊 Audio duration: {audio_duration:.2f}s")
    
    # Convert paths to relative for Windows FFmpeg compatibility
    try:
        video_rel = os.path.relpath(video_path, os.getcwd())
        audio_rel = os.path.relpath(audio_path, os.getcwd())
        output_rel = os.path.relpath(output_path, os.getcwd())
    except ValueError:
        # If relpath fails (different drives), use absolute paths
        video_rel = video_path
        audio_rel = audio_path
        output_rel = output_path
    
    # FFmpeg command with maximum compatibility encoding
    # Re-encode video to H.264 baseline for Windows Media Player compatibility
    # -map 0:v:0 = take video from first input
    # -map 1:a:0 = take audio from second input
    # -c:v libx264 = H.264 video codec
    # -profile:v baseline = Maximum compatibility profile
    # -level 3.0 = Works on all devices
    # -pix_fmt yuv420p = Standard color format
    # -c:a aac -b:a 192k = AAC audio with good bitrate
    # -ac 2 = Stereo audio
    # -ar 44100 = Standard sample rate
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-i", video_rel,
        "-i", audio_rel,
        "-map", "0:v:0",  # Explicitly map video stream
        "-map", "1:a:0",  # Explicitly map audio stream
        "-c:v", "libx264",  # H.264 video codec
        
        "-profile:v", "baseline",  # Higher quality profile
        "-level", "3.0",  # Supports higher quality
        "-b:v", "5000k",  # Higher video bitrate for better quality
        "-pix_fmt", "yuv420p",  # Standard pixel format
        "-c:a", "aac",    # AAC audio codec
        "-b:a", "192k",   # Audio bitrate
        "-ac", "2",       # Stereo
        "-ar", "44100",   # Sample rate
        # "-shortest",      # REMOVED: Do not cut audio if video is shorter
        "-movflags", "+faststart",  # Enable streaming/fast playback start
        output_rel
    ]
    
    print(f"🎬 Running FFmpeg: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return False, f"FFmpeg error:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        
        if not os.path.exists(output_path):
            return False, "FFmpeg completed but output file not found"
        
        # Verify output has both video and audio streams
        has_audio, verification_msg = verify_video_has_audio(output_path)
        if not has_audio:
            return False, f"Output video missing audio: {verification_msg}"
        
        print(f"✅ Video with audio created: {output_path}")
        return True, output_path
        
    except subprocess.TimeoutExpired:
        return False, "FFmpeg timed out after 120 seconds"
    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg and add to PATH."
    except Exception as e:
        return False, f"FFmpeg exception: {e}"


def verify_video_has_audio(video_path: str) -> Tuple[bool, str]:
    """Verify the video file contains an audio stream."""
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a',  # Select only audio streams
                '-show_entries', 'stream=codec_type',
                '-of', 'csv=p=0',
                video_path
            ],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and 'audio' in result.stdout:
            return True, "Audio stream found"
        else:
            return False, f"No audio stream detected. ffprobe output: {result.stdout} {result.stderr}"
    except Exception as e:
        return False, f"Could not verify audio: {e}"


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not get audio duration: {e}")
    return 0.0


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not get video duration: {e}")
    return 0.0


def test_audio_overlay():
    """Test function to verify audio overlay works."""
    print("=" * 60)
    print("AUDIO OVERLAY TEST")
    print("=" * 60)
    
    # Check if FFmpeg is installed
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        print(f"✅ FFmpeg found: {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        print("❌ FFmpeg not found! Please install FFmpeg.")
        return False
    
    # Check if ffprobe is installed
    try:
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True)
        print(f"✅ ffprobe found: {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        print("❌ ffprobe not found! Please install FFmpeg.")
        return False
    
    return True


if __name__ == "__main__":
    test_audio_overlay()