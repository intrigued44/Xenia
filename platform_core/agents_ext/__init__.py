import os
import json
from anthropic import Anthropic
import httpx

def call_claude(prompt: str, max_tokens: int = 800) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "mock_key")
    
    if api_key == "mock_key":
        # For testing
        client = Anthropic(
            api_key="mock_key",
            http_client=httpx.Client(
                transport=httpx.MockTransport(lambda r: httpx.Response(200, json={
                    "content": [{"text": "{\"mock\": \"data\"}"}]
                }))
            )
        )
    else:
        client = Anthropic(api_key=api_key)
        
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text.strip()
    
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
            
    return text.strip()
