import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize local model
generator = pipeline("text-generation", model="distilgpt2", device=-1)  # CPU

# Request model
class ChatRequest(BaseModel):
    message: str

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Add system prompt
        system_prompt = (
            "You are a friendly and helpful chatbot. Respond to user messages in a conversational, concise, and relevant manner. "
            "If the user says something short like 'hi', greet them back warmly and ask how you can assist."
        )
        full_input = f"{system_prompt}\nUser: {request.message}\nAssistant:"
        result = generator(full_input, max_new_tokens=150, temperature=0.7, return_full_text=False)
        return {"response": result[0]["generated_text"].strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}