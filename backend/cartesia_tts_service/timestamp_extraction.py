# tts_service/timestamp_extraction.py

from typing import List, Dict


def map_timepoints_to_beats(
    timepoints: List[dict], 
    expected_beats: List[str]
) -> Dict[str, float]:
    """
    Map word-level timestamps to beat markers.
    
    DEPRECATED: Use map_cartesia_timestamps_to_beats() for Cartesia TTS
    
 
    
    Inputs:
      - timepoints: List of dicts from TTS with 'mark_name' and 'time_seconds'.
      - expected_beats: List of expected beat mark names in order.

    Outputs:
      - Dict mapping beat mark names to actual time_offsets (in seconds).
      - If a mark name is missing, it's omitted.
    """
    # Create mapping mark_name -> time_seconds
    timepoint_map = {tp["mark_name"]: tp["time_seconds"] for tp in timepoints if "mark_name" in tp}

    beat_timing = {}
    for beat_name in expected_beats:
        if beat_name in timepoint_map:
            beat_timing[beat_name] = timepoint_map[beat_name]

    return beat_timing


def map_cartesia_timestamps_to_beats(
    timepoints: List[dict],
    expected_beats: List[str]
) -> Dict[str, float]:
    """
    Map Cartesia word-level timestamps to beat markers.
    
    Cartesia provides word-level timing: [{'word': 'hello', 'time_seconds': 0.5, 'duration': 0.2}, ...]
    Distribute beats evenly across the total audio duration.
    
    Inputs:
      - timepoints: List of dicts with 'word', 'time_seconds', 'duration'
      - expected_beats: List of expected beat IDs (beat1, beat2, ...)
    
    Outputs:
      - Dict mapping beat names to their start times
    """
    if not timepoints:
        # Fallback: assume beats are 5 seconds apart
        return {beat: i * 5.0 for i, beat in enumerate(expected_beats)}
    
    # Get total duration from last word
    total_duration = timepoints[-1]['time_seconds'] + timepoints[-1]['duration']
    beat_duration = total_duration / len(expected_beats) if expected_beats else total_duration
    
    # Map beats evenly across the duration
    beat_timing = {beat: i * beat_duration for i, beat in enumerate(expected_beats)}
    
    return beat_timing


def create_plain_transcript(beats: List[dict]) -> str:
    """
    Create plain text transcript from beats (no markers needed for Cartesia word-level timestamps).
    """
    text_parts = [beat.get("narration_text", "") for beat in beats]
    return " ".join(text_parts)


def extract_beat_times_from_transcript(
    transcript: str,
    timepoints: List[dict]
) -> Dict[str, float]:
    """
    Extract beat timing from a transcript with beat markers and word-level timestamps.
    
    Scans the transcript for beat markers (e.g., "beat1:", "beat2:") and finds the 
    corresponding word in the timepoints list to determine exact timing.
    
    Args:
        transcript: Text with beat markers like "beat1: text here. beat2: more text."
        timepoints: Cartesia word-level timestamps
    
    Returns:
        Dict mapping beat IDs to their start times
    """
    beat_timing = {}
    
    # Split transcript into beats
    import re
    beat_pattern = r'(beat\d+):\s*'
    beats = re.split(beat_pattern, transcript)
    
    # beats will be like ['', 'beat1', 'text...', 'beat2', 'text...']
    for i in range(1, len(beats), 2):
        if i < len(beats):
            beat_id = beats[i]
            beat_text = beats[i + 1] if i + 1 < len(beats) else ""
            
            # Find first word of this beat in timepoints
            first_words = beat_text.split()[:3]  # Get first few words
            
            for tp in timepoints:
                if any(word.lower() in tp['word'].lower() for word in first_words):
                    beat_timing[beat_id] = tp['time_seconds']
                    break
    
    return beat_timing
