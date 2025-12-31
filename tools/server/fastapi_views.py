import io
import os
from http import HTTPStatus

import soundfile as sf
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from fish_speech.utils.schema import ServeTTSRequest
from tools.server.fastapi_utils import (
    buffer_to_async_generator,
    get_content_type,
    inference_async,
)
from tools.server.inference import inference_wrapper as inference
from tools.server.model_manager import ModelManager

router = APIRouter()

@router.get("/v1/health")
@router.post("/v1/health")
async def health():
    return {"status": "ok"}

@router.post("/v2/tts")
async def tts(req: ServeTTSRequest, request: Request):
    """
    Generate speech from text using TTS model.
    """
    try:
        # Get the model from the app
        app_state = request.app.state
        model_manager: ModelManager = app_state.model_manager
        engine = model_manager.tts_inference_engine
        sample_rate = engine.decoder_model.sample_rate

        # Check if the text is too long
        if hasattr(app_state, "max_text_length") and app_state.max_text_length > 0 and len(req.text) > app_state.max_text_length:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Text is too long, max length is {app_state.max_text_length}",
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
