from typing import Annotated, Any

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, Response
from loguru import logger
from fish_speech.utils.schema import ServeTTSRequest
from fish_speech.inference_engine.inference_wrapper import inference_wrapper as inference

async def inference_async(req: ServeTTSRequest, engine):
    for chunk in inference(req, engine):
        if isinstance(chunk, bytes):
            yield chunk

async def buffer_to_async_generator(buffer):
    yield buffer

def get_content_type(audio_format):
    if audio_format == "wav":
        return "audio/wav"
    elif audio_format == "flac":
        return "audio/flac"
    elif audio_format == "mp3":
        return "audio/mpeg"
    else:
        return "application/octet-stream"
