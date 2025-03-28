import modal
from transformers import pipeline

# Name of your Modal app
stub = modal.Stub("summarizer-service")

# Define Docker image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install("transformers", "torch", "accelerate", "scipy")
)

# Define the summarization function
@stub.function(image=image, timeout=120)
def summarize(text: str, max_length: int = 150, min_length: int = 30) -> str:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return result[0]["summary_text"]
