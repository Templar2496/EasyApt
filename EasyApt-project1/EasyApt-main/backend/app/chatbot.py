"""
AI Medical Assistant Chatbot using Groq
Provides general health information with appropriate disclaimers
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
from .config import settings
from .auth import get_current_user
from .models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize Groq client
try:
    client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info(" Groq AI client initialized")
except Exception as e:
    logger.warning(f"Groq client not initialized: {e}")
    client = None

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    disclaimer: str

SYSTEM_PROMPT = """You are a helpful medical information assistant for EasyApt, a healthcare appointment scheduling platform. 

CRITICAL RULES - You MUST follow these:

1. You provide GENERAL health information only - never diagnose, prescribe, or give personalized medical advice
2. ALWAYS remind users that you're not a substitute for professional medical care
3. For ANY specific symptoms or health concerns, encourage users to book an appointment through EasyApt
4. In emergencies, tell users to call 911 or go to the emergency room immediately
5. Keep responses concise (2-4 paragraphs maximum)
6. Be friendly, empathetic, and encouraging
7. Base responses on evidence-based health information

Topics you can discuss:
- General information about common conditions (flu, cold, etc.)
- Healthy lifestyle tips (sleep, exercise, nutrition)
- When to seek medical attention
- How to use the EasyApt appointment system
- General wellness and prevention

Topics you CANNOT discuss:
- Specific diagnoses for user symptoms
- Medication recommendations or dosages
- Treatment plans
- Medical test interpretation
- Anything requiring a medical license

Response format:
1. Provide helpful general information
2. Encourage booking appointment if applicable
3. Always end with reminder about professional medical care

Remember: Your goal is to educate and guide users to appropriate care, not replace healthcare providers."""

MEDICAL_DISCLAIMER = """⚠️IMPORTANT: This information is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified healthcare provider with any questions you may have regarding a medical condition. In case of emergency, call 911 immediately."""

@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """
    AI chatbot endpoint using Groq
    Requires authentication - only logged-in users can access
    """
    
    if not client:
        raise HTTPException(
            status_code=503,
            detail="AI chatbot service is currently unavailable. Please try again later."
        )
    
    try:
        logger.info(f" Chatbot query from {current_user.email}: {chat_message.message[:50]}...")
        
        # Call Groq API with Llama 3 model
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": chat_message.message
                }
            ],
            model="llama-3.3-70b-versatile",  # Fast and intelligent model
            temperature=0.7,  # Balanced creativity
            max_tokens=500,  # Limit response length
        )
        
        # Extract response
        response_text = chat_completion.choices[0].message.content
        
        logger.info(f" Chatbot response generated for {current_user.email}")
        
        return ChatResponse(
            response=response_text,
            disclaimer=MEDICAL_DISCLAIMER
        )
        
    except Exception as e:
        logger.error(f" Chatbot error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response. Please try again."
        )

@router.get("/health")
async def chatbot_health():
    """Check if chatbot service is available"""
    return {
        "status": "available" if client else "unavailable",
        "model": "llama-3.3-70b-versatile" if client else None,
        "provider": "Groq"
    }
