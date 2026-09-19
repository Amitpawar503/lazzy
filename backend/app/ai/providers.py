"""Registry of free / freemium AI providers.

Phase 4 (the multi-agent analysis layer) will route through whichever of these
have a key set. This module just reports availability so the UI/API can show
what's wired — no network calls yet. All are free or have a usable free tier;
Ollama needs no key at all.
"""
from __future__ import annotations

from app.config import get_settings

# name, kind, env/setting attribute, free-tier note, docs
_CATALOG = [
    ("Groq", "llm", "groq_api_key", "Free tier, very fast (Llama/Mixtral)", "https://console.groq.com"),
    ("Google Gemini", "llm", "gemini_api_key", "Free tier via Google AI Studio", "https://aistudio.google.com"),
    ("Together AI", "llm", "together_api_key", "Free credits, many OSS models", "https://api.together.xyz"),
    ("Hugging Face", "llm", "hf_token", "Free Inference API", "https://huggingface.co/settings/tokens"),
    ("NVIDIA NIM", "llm", "nvidia_api_key", "Free credits", "https://build.nvidia.com"),
    ("Cloudflare Workers AI", "llm", "cloudflare_api_token", "Free daily allocation", "https://developers.cloudflare.com/workers-ai"),
    ("OpenRouter", "llm", "openrouter_api_key", "Has :free models", "https://openrouter.ai"),
    ("Mistral", "llm", "mistral_api_key", "Free tier", "https://console.mistral.ai"),
    ("Cerebras", "llm", "cerebras_api_key", "Free tier, fast inference", "https://cloud.cerebras.ai"),
    ("SambaNova Cloud", "llm", "sambanova_api_key", "Free tier", "https://cloud.sambanova.ai"),
    ("Zhipu GLM", "llm", "glm_api_key", "Free tier", "https://open.bigmodel.cn"),
    ("Ollama (local)", "llm", "ollama_base_url", "Runs locally, no key", "https://ollama.com"),
    ("Black Forest Labs", "image", "bfl_api_key", "Free credits (image gen)", "https://blackforestlabs.ai"),
    ("fal.ai", "image", "fal_api_key", "Free credits (media)", "https://fal.ai"),
]


def list_providers() -> dict:
    s = get_settings()
    providers = []
    for name, kind, attr, note, url in _CATALOG:
        providers.append(
            {
                "name": name,
                "kind": kind,
                "configured": bool(getattr(s, attr, None)),
                "free_note": note,
                "docs": url,
            }
        )
    configured = [p["name"] for p in providers if p["configured"]]
    return {
        "total": len(providers),
        "configured_count": len(configured),
        "configured": configured,
        "providers": providers,
    }
