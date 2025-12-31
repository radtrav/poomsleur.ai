from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fish_speech.inference_engine.manager import ModelManager
from fish_speech.api.config import settings

# Global state for ModelManager (initialized in lifespan)
_model_manager: ModelManager | None = None

def get_model_manager() -> ModelManager:
    if _model_manager is None:
        raise RuntimeError("ModelManager is not initialized")
    return _model_manager

# Security scheme
security = HTTPBearer(auto_error=False)

async def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    if settings.api_key is None:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
