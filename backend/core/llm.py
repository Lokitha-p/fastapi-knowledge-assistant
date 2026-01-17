import requests
import json
import time
from backend.config.settings import OPENROUTER_API_KEY, OPENROUTER_API_BASE, LLM_MODEL, USE_MOCK_LLM


class MockLLM:
    """Mock LLM for testing without API key"""

    def __init__(self):
        print("✅ Mock LLM initialized (no API key required)")

    def invoke(self, prompt: str) -> str:
        """
        Return mock responses based on the prompt content
        """
        print(f"🔄 Mock LLM processing prompt (length: {len(prompt)} chars)")

        # Detect what kind of response is needed based on prompt keywords
        prompt_lower = prompt.lower()

        if "extract topics" in prompt_lower or "identify the 3 most important topics" in prompt_lower:
            # For topic extraction - return JSON array
            response = '["Getting Started with FastAPI", "Request Validation and Models", "Database Integration"]'

        elif "generate" in prompt_lower and "faqs" in prompt_lower and "knowledge base" in prompt_lower:
            # For new knowledge-base FAQ generation with citations
            response = """[
  {
    "question": "What is the main purpose of this feature?",
    "answer": "Based on the knowledge base, this feature provides core functionality for the application. [Source: Document 1]",
    "sources": ["Document 1"]
  },
  {
    "question": "How do I implement this feature?",
    "answer": "According to the documentation, you can implement this by following the standard pattern shown in the examples. [Source: Document 2]",
    "sources": ["Document 2"]
  },
  {
    "question": "What are the best practices?",
    "answer": "The knowledge base recommends following type hints and using async patterns for better performance. [Source: Document 1]",
    "sources": ["Document 1"]
  }
]"""

        elif "convert this specific stackoverflow question" in prompt_lower or "generalized pattern" in prompt_lower:
            # For question generalization - extract the question and generalize it
            if "Question:" in prompt:
                question = prompt.split("Question:")[-1].strip().split("\n")[0]
                # Simple generalization logic
                question = question.replace("FastAPI", "<framework>")
                question = question.replace("PostgreSQL", "<database>")
                question = question.replace("MongoDB", "<database>")
                question = question.replace("SQLAlchemy", "<ORM>")
                question = question.replace("OAuth2", "<auth mechanism>")
                question = question.replace("JWT", "<token type>")
                question = question.replace("401", "<error code>")
                question = question.replace("404", "<error code>")
                question = question.replace("500", "<error code>")
                response = question
            else:
                response = "How to use <feature> in <framework>?"

        elif "summarize" in prompt_lower or "summary" in prompt_lower:
            # For summarization
            response = "FastAPI is a modern Python web framework designed for building APIs quickly and efficiently. It provides automatic documentation, type checking, and high performance."

        else:
            # Generic response
            response = "This is a mock response for testing. In production, replace with actual LLM API."

        print(f"✅ Mock LLM generated response (length: {len(response)} chars)")
        return response

    def __call__(self, prompt: str) -> str:
        """Make the object callable"""
        return self.invoke(prompt)


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
            "Content-Type": "application/json",
            "HTTP-Referer": "https://fastapi-knowledge-assistant.local",
            "X-Title": "FastAPI Knowledge Assistant"
        }

        print(f"🔄 Calling OpenRouter API with model: {self.model}")
        print(f"📍 URL: {url}")
        print(f"🔑 API Key: {self.api_key[:40]}...")
        print(f"📦 Payload model: {payload['model']}")

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
    Initialize and return an LLM instance for general use.
    Uses Mock LLM if USE_MOCK_LLM=true, otherwise OpenRouter.
    """
    if USE_MOCK_LLM:
        print("🔧 Using Mock LLM (testing mode)")
        return MockLLM()
    else:
        print("🔧 Using OpenRouter LLM (production mode)")
        llm = OpenRouterLLM(api_key=OPENROUTER_API_KEY, model=LLM_MODEL)
        return llm


def get_faq_llm():
    """
    Initialize and return a separate LLM instance for FAQ agent.
    Uses Mock LLM if USE_MOCK_LLM=true, otherwise OpenRouter.
    """
    if USE_MOCK_LLM:
        print("🔧 Using Mock LLM for FAQ agent (testing mode)")
        return MockLLM()
    else:
        print("🔧 Using OpenRouter LLM for FAQ agent (production mode)")
        llm = OpenRouterLLM(api_key=OPENROUTER_API_KEY, model=LLM_MODEL)
        return llm
