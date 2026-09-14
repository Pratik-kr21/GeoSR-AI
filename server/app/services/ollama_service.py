import httpx
from app.config import settings

class OllamaService:
    @staticmethod
    async def generate_response(prompt: str, context: dict = None) -> str:
        # Construct payload for local Ollama instance
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{settings.OLLAMA_HOST}/api/generate", json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "Error: No response field in Ollama output")
        except Exception as e:
            return f"Error communicating with local GeoAssist (Ollama): {str(e)}"

ollama_service = OllamaService()
