import re
import pyrootutils
import uvicorn
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Setup root path
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

from tools.server.model_manager import ModelManager
from tools.server.fastapi_views import router
from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--mode", type=str, choices=["tts"], default="tts")
    parser.add_argument(
        "--llama-checkpoint-path",
        type=str,
        default="checkpoints/openaudio-s1-mini",
    )
    parser.add_argument(
        "--decoder-checkpoint-path",
        type=str,
        default="checkpoints/openaudio-s1-mini/codec.pth",
    )
    parser.add_argument("--decoder-config-name", type=str, default="modded_dac_vq")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--max-text-length", type=int, default=0)
    parser.add_argument("--listen", type=str, default="127.0.0.1:8080")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--api-key", type=str, default=None)

    return parser.parse_args()

# Define arguments
args = parse_args()

# Security scheme
security = HTTPBearer(auto_error=False)

async def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    if args.api_key is None:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != args.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing ModelManager...")
    app.state.model_manager = ModelManager(
        mode=args.mode,
        device=args.device,
        half=args.half,
        compile=args.compile,
        llama_checkpoint_path=args.llama_checkpoint_path,
        decoder_checkpoint_path=args.decoder_checkpoint_path,
        decoder_config_name=args.decoder_config_name,
    )
    app.state.device = args.device
    app.state.max_text_length = args.max_text_length
    logger.info(f"Startup done, listening server at http://{args.listen}")
    
    yield
    
    # Shutdown logic (if any)
    logger.info("Shutting down...")

app = FastAPI(
    title="Fish Speech API",
    version="1.5.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_token)] if args.api_key else None
)

# CORS Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    # Parse host and port
    match = re.search(r"\[([^\]]+)\]:(\d+)$", args.listen)
    if match:
        host, port = match.groups()  # IPv6
    else:
        host, port = args.listen.split(":")  # IPv4

    uvicorn.run(
        "tools.fastapi_server:app",
        host=host,
        port=int(port),
        workers=args.workers,
        log_level="info",
    )
