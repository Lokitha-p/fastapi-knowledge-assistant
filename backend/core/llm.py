from transformers import pipeline

def get_llm():
    return pipeline(
        "text-generation",
        model="google/flan-t5-base",
        max_new_tokens=300
    )
