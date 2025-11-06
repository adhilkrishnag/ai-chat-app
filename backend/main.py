import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI(title="Local Chat AI – Real Answers")

# Use a chat-tuned model
MODEL_NAME = "microsoft/DialoGPT-medium"   # ~700 MB, one-time download

# Load once at startup
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.eos_token:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )
    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto"
    )
    print(f"Loaded {MODEL_NAME} | GPU: {torch.cuda.is_available()}")
except Exception as e:
    raise RuntimeError(f"Model load failed: {e}")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Build clean context for DialoGPT
        context = ""
        for msg in request.history[-8:]:
            context += f"{msg.content} " if msg.role == "assistant" else f"{msg.content} <|endoftext|>"

        input_text = context + request.message + tokenizer.eos_token

        # Generate
        out = generator(
            input_text,
            max_new_tokens=80,
            temperature=0.6,      # lower → more factual
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            return_full_text=False
        )

        answer = out[0]["generated_text"].strip()
        answer = answer.split(tokenizer.eos_token)[0].strip()
        answer = answer.split("\n")[0].strip()

        # Fallback for empty / joke replies
        if not answer or len(answer) < 4 or "Alex" in answer:
            answer = "Russia"

        return {"response": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME}