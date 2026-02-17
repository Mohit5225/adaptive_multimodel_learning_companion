import os
import asyncio
import base64
import json
from typing import List, Tuple, Dict
from cartesia import AsyncCartesia
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CartesiaTTSClient:
    def __init__(self):
        """Initialize Cartesia TTS client. Uses CARTESIA_API_KEY env var automatically."""
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            raise ValueError("❌ CARTESIA_API_KEY environment variable not set!")
        
        # Use AsyncCartesia for WebSocket support
        self.client = AsyncCartesia(api_key=api_key)

    def synthesize_with_timestamps(
        self,
        transcript: str,
        voice_params: dict,
        audio_config_params: dict
    ) -> Tuple[bytes, List[dict]]:
        """
        Synthesize text to speech with word-level timestamps using Cartesia SSE.
        
        NOTE: The SSE endpoint ONLY supports 'raw' (PCM) audio. 
        If 'mp3' is requested in audio_config_params, it will be overridden to 'raw'.
        """
        model_id = "sonic-3"
        
        try:
            # Use async context to get timestamps via WebSocket
            audio_bytes, timepoints = asyncio.run(
                self._synthesize_async(
                    model_id=model_id,
                    transcript=transcript,
                    voice=voice_params,
                    output_format=audio_config_params
                )
            )
            return audio_bytes, timepoints
            
        except Exception as e:
            print(f"❌ Cartesia API error: {e}")
            raise

    async def _synthesize_async(
        self,
        model_id: str,
        transcript: str,
        voice: dict,
        output_format: dict
    ) -> Tuple[bytes, List[dict]]:
        """
        Async SSE-based synthesis with streaming timestamps.
        """
        audio_chunks = []
        timepoints = []
        
        # FIX: SSE endpoint also requires 'raw' container for timestamps? 
        # The user snippet uses "container": "raw", "encoding": "pcm_f32le".
        ws_output_format = output_format.copy()
        if ws_output_format.get("container") != "raw":
            print("⚠️  SSE requires 'raw' container. Overriding output format to raw/pcm_f32le.")
            ws_output_format["container"] = "raw"
            ws_output_format["encoding"] = "pcm_f32le"
            ws_output_format["sample_rate"] = int(output_format.get("sample_rate", 44100))

        try:
            # Use SSE instead of WebSocket
            sse_iterator = self.client.tts.sse(
                model_id=model_id,
                transcript=transcript,
                voice=voice,
                output_format=ws_output_format,
                add_timestamps=True
            )

            async for event in sse_iterator:
                # 1. Handle Audio (Decode Base64)
                raw_data = getattr(event, 'data', None)
                
                if raw_data:
                    if isinstance(raw_data, str):
                        try:
                            decoded_chunk = base64.b64decode(raw_data)
                            audio_chunks.append(decoded_chunk)
                        except Exception:
                            pass
                    elif isinstance(raw_data, bytes):
                        audio_chunks.append(raw_data)
                
                # 2. Handle Timestamps
                chunk_timestamps = getattr(event, 'word_timestamps', None)
                
                if chunk_timestamps:
                    words = []
                    starts = []
                    ends = []
                    
                    if hasattr(chunk_timestamps, 'words'):
                        words = chunk_timestamps.words
                        starts = chunk_timestamps.start
                        ends = chunk_timestamps.end
                    elif isinstance(chunk_timestamps, dict):
                        words = chunk_timestamps.get('words', [])
                        starts = chunk_timestamps.get('start', [])
                        ends = chunk_timestamps.get('end', [])

                    if words:
                        for w, s, e in zip(words, starts, ends):
                            timepoints.append({
                                'word': w,
                                'time_seconds': float(s),
                                'duration': float(e - s)
                            })
            
            audio_bytes = b''.join(audio_chunks)
            return audio_bytes, timepoints
            
        except Exception as e:
            print(f"❌ SSE streaming error: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ Falling back to bytes() endpoint (timestamps unavailable)")
            return await self._synthesize_bytes_async(model_id, transcript, voice, output_format), []

    async def _synthesize_bytes_async(self, model_id, transcript, voice, output_format):
        audio_chunks = []
        async for chunk in self.client.tts.bytes(
            model_id=model_id,
            transcript=transcript,
            voice=voice,
            output_format=output_format
        ):
            audio_chunks.append(chunk)
        return b''.join(audio_chunks)

    def synthesize_bytes_only(
        self,
        transcript: str,
        voice_params: dict,
        audio_config_params: dict
    ) -> bytes:
        """
        Simple synchronous synthesis without timestamps (fallback method).
        """
        model_id = "sonic-3"
        try:
            return asyncio.run(
                self._synthesize_bytes_async(
                    model_id=model_id,
                    transcript=transcript,
                    voice=voice_params,
                    output_format=audio_config_params
                )
            )
        except Exception as e:
            print(f"❌ Cartesia bytes() error: {e}")
            raise