# tts_service/timestamp_extraction.py

from typing import List, Dict


def map_timepoints_to_beats(
    timepoints: List[dict], 
    expected_beats: List[str]
) -> Dict[str, float]:
    """
    Inputs:
      - timepoints: List of dicts from TTS with 'mark_name' and 'time_seconds'.
      - expected_beats: List of expected beat mark names in order.

    Outputs:
      - Dict mapping beat mark names to actual time_offsets (in seconds).
      - If a mark name is missing, it's omitted.
    """
    # Create mapping mark_name -> time_seconds
    timepoint_map = {tp["mark_name"]: tp["time_seconds"] for tp in timepoints}

    beat_timing = {}
    for beat_name in expected_beats:
        if beat_name in timepoint_map:
            beat_timing[beat_name] = timepoint_map[beat_name]

    return beat_timing


def create_ssml_with_marks(beats: List[dict]) -> str:
    """
    Given a list of beats (each has 'beat_id' and 'narration_text'), returns SSML string with 
    <mark> elements preceding each beat and pauses for complex math.

    Example input:
    [
        {"beat_id": "beat1", "narration_text": "Intro..."},
        {"beat_id": "beat2", "narration_text": "Next..."},
    ]

    Output SSML:
    <speak>
      <mark name="beat1"/><prosody rate="0.90">Intro...</prosody><break time="1000ms"/>
      <mark name="beat2"/><prosody rate="0.90">Next...</prosody><break time="800ms"/>
    </speak>
    """
    ssml_parts = ["<speak>"]
    for beat in beats:
        mark_name = beat.get("beat_id", f"beat{beats.index(beat)+1}")
        text = beat.get("narration_text", "")
        # Wrap with prosody for slower speech and add pauses between beats
        ssml_parts.append(f'<mark name="{mark_name}"/><prosody rate="0.90">{text}</prosody><break time="1000ms"/>')
    ssml_parts.append("</speak>")
    return "\n".join(ssml_parts)
