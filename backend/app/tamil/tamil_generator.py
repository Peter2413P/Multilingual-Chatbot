import json
from typing import List, Dict, AsyncGenerator
from app.rag.llm import get_llm
from app.tamil.tamil_retriever import retrieve_tamil_context

TAMIL_SYSTEM_PROMPT = """நீங்கள் தமிழ் மொழி AI உதவியாளர் (PersonaForge AI). 
வழங்கப்பட்டுள்ள சூழல் குறிப்புகளை (Context) அடிப்படையாகக் கொண்டு பயனரின் கேள்விக்குத் துல்லியமாகவும் தெளிவாகவும் தமிழில் மட்டுமே பதிலளிக்கவும்.

விதிகள்:
1. எப்போதும் தூய மற்றும் இயல்பான தமிழில் பதிலளிக்கவும்.
2. சூழலில் (Context) உள்ள தகவல்களைப் பயன்படுத்தி பதிலளிக்கவும்.
3. சூழலில் தகவல் இல்லையென்றால், "வழங்கப்பட்ட ஆவணங்களில் இதற்கான தகவல் கிடைக்கவில்லை" என்று நேர்மையாகக் கூறவும்.
4. பயனர் ஆங்கிலத்தில் கேட்காத வரை பதிலை ஆங்கிலத்தில் மொழிபெயர்க்க வேண்டாம்."""

async def stream_tamil_chat_response(
    persona_id: str,
    message: str,
    history: List[Dict[str, str]]
) -> AsyncGenerator[str, None]:
    """
    Streams LLM response in Tamil using context retrieved from the Tamil Chroma collection.
    """
    llm = get_llm()
    
    # 1. Retrieve Tamil context
    context, sources = retrieve_tamil_context(
        query=message,
        persona_id=persona_id,
        top_k=4
    )
    
    # 2. Yield sources first (matches existing frontend SSE protocol)
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
    
    # 3. Construct Tamil RAG prompt
    prompt = f"{TAMIL_SYSTEM_PROMPT}\n\n"
    
    if context:
        prompt += f"### சூழல் தகவல்கள் (Context):\n{context}\n\n"
        
    # Include recent conversation history if present
    if history:
        prompt += "### உரையாடல் வரலாறு:\n"
        for h in history[-4:]:
            role = "பயனர்" if h.get("role") == "user" else "உதவியாளர்"
            prompt += f"{role}: {h.get('content', '')}\n"
        prompt += "\n"
        
    prompt += f"பயனர் கேள்வி: {message}\nதமிழில் பதில்:"
    
    # 4. Stream LLM tokens
    try:
        for chunk in llm.stream(prompt):
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
