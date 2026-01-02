import io
import soundfile as sf  # type: ignore
import numpy as np
from typing import Annotated
from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from loguru import logger

from fish_speech.utils.schema import ServeTTSRequest, ServeTTSPairRequest
from fish_speech.api.config import settings
from fish_speech.api.deps import get_model_manager
from fish_speech.api.utils import (
    buffer_to_async_generator,
    get_content_type,
)
from fish_speech.inference_engine.inference_wrapper import inference_wrapper as inference
from fish_speech.inference_engine.manager import ModelManager

router = APIRouter()


def validate_length(max_length: int, text: str):
    # there is no max length
    if max_length <= 0:
        return

    text_length = len(text)

    if text_length > max_length:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Text of length {text_length} is too long, max length is {max_length}",
        )


@router.post("/v1/tts")
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
        validate_length(settings.max_text_length, req.text)

        # Perform TTS
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

@router.post("/v1/tts-pair")
async def tts_pair(
    req: ServeTTSPairRequest, 
    model_manager: Annotated[ModelManager, Depends(get_model_manager)]
):
    """
    Generate speech from text using TTS model.
    """
    try:
        engine = model_manager.tts_inference_engine
        sample_rate = engine.decoder_model.sample_rate

        # Check if the text is too long
        validate_length(settings.max_text_length, req.text_lang1)
        validate_length(settings.max_text_length, req.text_lang2)

        text_lang1_req = ServeTTSRequest(text= req.text_lang1)
        text_lang2_req = ServeTTSRequest(text= req.text_lang2)

        # Perform TTS
        audio1 = next(inference(text_lang1_req, engine))
        audio2 = next(inference(text_lang2_req, engine))

        # Create silence (e.g. 0.5 seconds)
        silence_duration = 1
        silence_samples = int(sample_rate * silence_duration)
        silence = np.zeros(silence_samples, dtype=audio1.dtype)

        # Concatenate: Audio 1 + Silence + Audio 2
        combined_audio = np.concatenate((audio1, silence, audio2))

        buffer = io.BytesIO()
        sf.write(
            buffer,
            combined_audio,
            sample_rate,
            format=text_lang1_req.format,
        )

        return StreamingResponse(
            buffer_to_async_generator(buffer.getvalue()),
            headers={
                "Content-Disposition": f"attachment; filename=audio.{text_lang1_req.format}",
            },
            media_type=get_content_type(text_lang1_req.format),
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Error in TTS generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to generate speech"
        )
