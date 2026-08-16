from platform_core.llm_provider import call_llm

def call_claude(prompt: str, max_tokens: int = 800) -> str:
    """
    Backward-compatible wrapper delegating to Xenia's unified call_llm provider abstraction.
    """
    return call_llm(prompt, max_tokens=max_tokens)
