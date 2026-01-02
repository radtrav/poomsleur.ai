# Poomsleur AI

Poomsleur AI is a specialized Text-to-Speech (TTS) API designed to assist with language learning and review. It mimics the functionality of language learning methods like Pimsleur by generating audio for language pairs and presenting them in a format optimized for study.

## Overview

The core purpose of this API is to facilitate the creation of audio review materials. It allows users to submit text in a source language and a target language, and returns a single, concatenated audio file.

### How It Works

1.  **Input**: The API accepts a request containing two text segments:
    *   `text_lang1`: The text in the source language (e.g., your native language).
    *   `text_lang2`: The text in the target language (e.g., the language you are learning).

    ```
    xh -d -o heya2.wav POST http://0.0.0.0:8080/v1/tts-pair \
  text_lang1="where are you?" \
  text_lang2="ou es tu?" 
    ```


1.  **Processing**:
    *   The system uses advanced TTS models to generate high-quality, natural-sounding speech for both text segments independently.
    *   It automatically inserts a silence interval (pause) between the two audio segments.

2.  **Output**:
    *   The API combines the source audio, the silence, and the target audio into a continuous stream.
    *   The result is a single WAV file that you can listen to, allowing you to hear the prompt, pause to think or repeat, and then hear the translation.

## Key Features

*   **Dual-Language Support**: Seamlessly handles text-to-speech generation for language pairs.
*   **Automatic Concatenation**: Intelligently merges audio files with appropriate spacing.
*   **Review-Ready Output**: Delivers audio files ready for immediate playback and study.

## Getting Started

### Prerequisites

*   Python installed
*   `uv` package manager

### Installation & Setup

1.  **Install Hugging Face CLI**:
    ```bash
    uv tool install huggingface_hub[cli]
    ```

2.  **Download Model Checkpoints**:
    ```bash
    hf download fishaudio/openaudio-s1-mini --local-dir checkpoints/openaudio-s1-mini
    ```

3.  **Run the Server**:
    ```bash
    uv run python -m fish_speech.api.main
    ```

The API will be available at `http://127.0.0.1:8080`.
