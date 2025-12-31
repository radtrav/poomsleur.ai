from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Settings
    project_name: str = "Fish Speech API"
    version: str = "1.5.0"
    
    # Server Settings
    listen: str = "127.0.0.1:8080"
    workers: int = 1
    api_key: Optional[str] = None
    
    # Model Settings
    mode: str = "tts"
    device: str = "cuda"
    half: bool = False
    compile: bool = False
    llama_checkpoint_path: str = "checkpoints/openaudio-s1-mini"
    decoder_checkpoint_path: str = "checkpoints/openaudio-s1-mini/codec.pth"
    decoder_config_name: str = "modded_dac_vq"
    max_text_length: int = 0

    model_config = SettingsConfigDict(
        env_prefix="FISH_SPEECH_",
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
