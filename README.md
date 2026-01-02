# Poomsleur is a ai application that imitates the functionality of Pimsleur

# uv tool install huggingface_hub[cli]

hf download fishaudio/openaudio-s1-mini --local-dir checkpoints/openaudio-s1-mini


uv run python -m fish_speech.api.main