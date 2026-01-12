import requests
import json
import time
from backend.config.settings import OPENROUTER_API_KEY, OPENROUTER_API_BASE, LLM_MODEL


class OpenRouterLLM:
    """Custom wrapper for OpenRouter API"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.api_base = OPENROUTER_API_BASE
        self.last_request_time = 0
        self.min_delay = 1  # 1 second between requests

        if not self.api_key or self.api_key == "":
            raise ValueError(
                "❌ OPENROUTER_API_KEY is not set!\n"
                "Please add it to your .env file:\n"
                "OPENROUTER_API_KEY=sk-or-your-actual-key"
            )

        print(f"✅ OpenRouter LLM initialized with model: {self.model}")
        print(f"✅ API Key loaded: {self.api_key[:30]}...")

    def invoke(self, prompt: str) -> str:
        """
        Call OpenRouter API and return the generated text
        """
        # Rate limiting: wait if needed
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            time.sleep(wait_time)

        url = f"{self.api_base}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://fastapi-knowledge-assistant.local",
            "X-Title": "FastAPI Knowledge Assistant"
        }

        print(f"🔄 Calling OpenRouter API with model: {self.model}")
        print(f"📍 URL: {url}")
        print(f"🔑 API Key: {self.api_key[:40]}...")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
            self.last_request_time = time.time()

            print(f"📡 OpenRouter Response Status: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")

            if response.status_code != 200:
                print(f"❌ Error Response: {response.text}")
                response.raise_for_status()

            result = response.json()
            print(f"✅ API Response received successfully")

            # Extract the text from OpenRouter response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                print(f"✅ Generated content length: {len(content)} characters")
                return content

            print("⚠️  No choices in response")
            return ""

        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {type(e).__name__}")
            print(f"❌ Error Details: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"❌ Response Status: {e.response.status_code}")
                print(f"❌ Response Body: {e.response.text}")
            raise

    def __call__(self, prompt: str) -> str:
        """Make the object callable"""
        return self.invoke(prompt)


def get_llm():
    """
    Initialize and return an OpenRouter LLM instance.
    """
    llm = OpenRouterLLM(api_key=OPENROUTER_API_KEY, model=LLM_MODEL)
    return llm
