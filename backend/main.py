import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Hugging Face API settings
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Set this in .env file
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B-Instruct"

# Request model
class ChatRequest(BaseModel):
    message: str

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    if not HF_API_TOKEN:
        raise HTTPException(status_code=500, detail="Hugging Face API token not set")

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": request.message,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "return_full_text": False,
        },
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return {"response": result[0]["generated_text"]}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling Hugging Face API: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}