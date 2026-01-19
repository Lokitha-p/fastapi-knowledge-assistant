--> Project Overview

One of the most common frustrations developers face is navigating technical documentation. Even when the docs are well written, finding a precise answer often means jumping across multiple pages, scanning long explanations, and piecing things together manually. After experiencing this myself many times, I wanted to build something that could make documentation easier to use, not just easier to read.

The FastAPI Knowledge Assistant turns static FastAPI documentation into an interactive system that understands natural language questions and responds with accurate, source-backed answers. It uses Retrieval-Augmented Generation (RAG) to ensure responses are grounded in real documentation rather than model assumptions. In addition to Q&A, the system can automatically generate summaries and developer-focused FAQs, reducing the time spent manually reading large sections of docs.

--> Why FastAPI Documentation?

High quality and structure – The docs are clean, well-organized, and maintained by FastAPI’s creator.
Technically rich – They include real code examples, best practices, and advanced concepts.
Practical relevance – FastAPI is widely used, so the assistant has real-world value.
Manageable scope – The 10 core tutorial pages are enough to demonstrate RAG effectively without unnecessary complexity.
The selected pages cover essential topics such as routing, request parameters, request bodies, file uploads, dependencies, security, middleware, and background tasks—everything a FastAPI developer regularly needs.

--> Architecture & Design Decisions
Agent-Based Architecture

Instead of building one large script, the system is divided into four specialized agents, each responsible for a specific task. This modular design makes the system easier to debug, extend, and maintain.

1. Ingestion Agent

This agent handles data collection and preparation. It scrapes FastAPI documentation using BeautifulSoup, removes irrelevant HTML elements like navigation bars and footers, and splits the content into chunks.

A chunk size of 1000 characters with overlap was chosen to balance context retention with retrieval accuracy. The cleaned text is then converted into embeddings and stored in ChromaDB.

2. Summary Agent

This agent generates concise, developer-focused summaries for each section and an overall executive summary. The prompts are designed to prioritize actionable information over generic descriptions. All outputs are stored in JSON format, making them reusable across different interfaces.

3. FAQ Agent

The FAQ agent identifies realistic questions that developers actually ask. To avoid generic or obvious questions, the prompts are tuned to focus on practical usage and common pitfalls.
StackOverflow queries were referenced to validate relevance, and each answer includes source citations for transparency.

4. RAG Agent

This is the core of the system. When a user asks a question, the agent:
Converts the query into an embedding
Retrieves the most relevant documentation chunks from ChromaDB
Injects that context into the LLM prompt
Generates an answer strictly based on retrieved content
If no relevant documentation is found, the system explicitly states that the information is unavailable, preventing hallucination.

--> Technology Choices
ChromaDB:
Chosen for its simplicity and local-first approach:
No external cloud dependency
Persistent storage
Easy Python integration
Suitable for small to medium datasets

SentenceTransformers (all-MiniLM-L6-v2):
This model offers a strong balance between speed and semantic understanding. It runs locally, performs well for technical text, and avoids API costs.

OpenRouter for LLM Access:
OpenRouter provides flexibility by supporting multiple models through a single interface. The project uses arcee-ai/trinity-mini for cost efficiency and includes a Mock LLM mode for testing without API usage.

FastAPI Backend:
Using FastAPI to build a FastAPI assistant felt appropriate. It provides:
Automatic API documentation
Strong type validation with Pydantic
Async request handling
Simple CORS configuration for frontend integration

React + Vite Frontend:
The frontend is intentionally minimal and responsive:
Vite for fast development
React for familiarity
Simple fetch-based data flow
Clean UI focused on readability

--> Key Design Decisions

RAG Instead of Fine-Tuning:
Fine-tuning would be costly and inflexible. RAG allows:
Instant updates by re-ingesting documents
Source attribution for every answer
Use of smaller models
Better transparency and control

Prompt Design:

The RAG prompt is structured to keep the model focused and grounded:

"You are a FastAPI expert assistant.
Use the following documentation context to answer the question.
Context: [retrieved chunks]
Question: [user query]
Answer:      "


This significantly reduces hallucination and improves answer relevance.

--> Error Handling & Honesty:
If relevant information is not found, the system responds honestly instead of guessing. This is critical for a documentation assistant where accuracy matters more than completeness.

--> Source Attribution:
Every response includes links to the original FastAPI documentation. This builds trust and allows users to explore topics in more depth.

--> Challenges & Solutions:
Scraping noise: Navigation elements polluted early embeddings
→ Solved by targeted HTML extraction with BeautifulSoup

Context window limits: Long pages exceeded LLM limits
→ Solved with chunking and top-3 retrieval

Generic FAQs: Early outputs lacked practical value
→ Solved through stricter prompts and StackOverflow validation

API rate limits: Free-tier constraints slowed testing
→ Solved with mock LLM mode and request throttling

Frontend integration issues: CORS and inconsistent responses
→ Solved using FastAPI middleware and strict Pydantic schemas


Conclusion:

The FastAPI Knowledge Assistant demonstrates how modern AI techniques can turn static documentation into an interactive, developer-friendly knowledge system. It is well-suited for small-scale production use and can be extended to larger documentation sets with architectural enhancements.
The project solves a real problem: helping developers find accurate answers quickly, so they can focus on building rather than searching.