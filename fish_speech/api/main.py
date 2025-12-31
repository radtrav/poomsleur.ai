import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from fish_speech.inference_engine.manager import ModelManager
from fish_speech.api.config import settings
from fish_speech.api.deps import verify_token
from fish_speech.api import deps
from fish_speech.api.routers import health, tts
from fish_speech.api.exception_handler import ExceptionHandler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing ModelManager...")
    # Initialize the global ModelManager instance
    deps._model_manager = ModelManager(
        mode=settings.mode,
        device=settings.device,
        half=settings.half,
        compile=settings.compile,
        llama_checkpoint_path=settings.llama_checkpoint_path,
        decoder_checkpoint_path=settings.decoder_checkpoint_path,
        decoder_config_name=settings.decoder_config_name,
    )
    
    logger.info(f"Startup done, listening server at http://{settings.listen}")
    
    yield
    
    # Shutdown logic (if any)
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    lifespan=lifespan,
    dependencies=[Depends(verify_token)] if settings.api_key else None
)

# CORS Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
handler = ExceptionHandler()
app.add_exception_handler(HTTPException, handler.http_exception_handler)
app.add_exception_handler(Exception, handler.other_exception_handler)

# Include routes
app.include_router(health.router)
app.include_router(tts.router)

if __name__ == "__main__":
    import re
    # Parse host and port from settings
    match = re.search(r"\[([^\]]+)\]:(\d+)$", settings.listen)
    if match:
        host, port = match.groups()  # IPv6
    else:
        host, port = settings.listen.split(":")  # IPv4

    uvicorn.run(
        "fish_speech.api.main:app",
        host=host,
        port=int(port),
        workers=settings.workers,
        log_level="info",
    )
