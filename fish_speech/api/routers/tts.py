import io
import soundfile as sf
from typing import Annotated
from http import HTTPStatus
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from loguru import logger

from fish_speech.utils.schema import ServeTTSRequest
from fish_speech.api.config import settings
from fish_speech.api.deps import get_model_manager
from fish_speech.api.utils import (
    buffer_to_async_generator,
    get_content_type,
    inference_async,
)
from fish_speech.inference_engine.inference_wrapper import inference_wrapper as inference
from fish_speech.inference_engine.manager import ModelManager

router = APIRouter()

@router.post("/v2/tts")
async def tts(
    req: ServeTTSRequest, 
    model_manager: Annotated[ModelManager, Depends(get_model_manager)]
):
    """
    Generate speech from text using TTS model.
    """
    try:
        engine = model_manager.tts_inference_engine
        sample_rate = engine.decoder_model.sample_rate

        # Check if the text is too long
        if settings.max_text_length > 0 and len(req.text) > settings.max_text_length:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Text is too long, max length is {settings.max_text_length}",
            )

        # Check if streaming is enabled
        if req.streaming and req.format != "wav":
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Streaming only supports WAV format",
            )

        # Perform TTS
        if req.streaming:
            return StreamingResponse(
                inference_async(req, engine),
                headers={
                    "Content-Disposition": f"attachment; filename=audio.{req.format}",
                },
                media_type=get_content_type(req.format),
            )
        else:
            fake_audios = next(inference(req, engine))
            buffer = io.BytesIO()
            sf.write(
                buffer,
                fake_audios,
                sample_rate,
                format=req.format,
            )

            return StreamingResponse(
                buffer_to_async_generator(buffer.getvalue()),
                headers={
                    "Content-Disposition": f"attachment; filename=audio.{req.format}",
                },
                media_type=get_content_type(req.format),
            )
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Error in TTS generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to generate speech"
        )
