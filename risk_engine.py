import sys
import time
import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()

DB_PATH = "vector_db"
MAX_RETRIES = 3
INITIAL_BACKOFF = 5

# ==========================================
# GLOBAL INITIALIZATION (Performance Fix)
# ==========================================
print("[ScamScope] Initializing embeddings and models into memory...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Using Llama 3.3 70B Versatile for maximum accuracy (Groq)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_retries=0,
    timeout=60,
)

prompt = ChatPromptTemplate.from_template(
    """
You are a cybersecurity risk assessment assistant.

Analyze the message below for scam risk using known scam patterns.
Assess risk — do NOT accuse.

RULES:
- Evaluate the user message as ONE complete unit
- Retrieved knowledge is supporting evidence only
- Be CONCISE: max 3 bullet points per section, explanation max 2-3 sentences

User Message:
{user_input}

Relevant Scam Knowledge:
{context}

Respond in EXACTLY this format (keep it short and direct):

Final Scam Risk Score: <number>/100

Primary Risk Indicators:
- <short bullet, max 12 words>
- <short bullet, max 12 words>
- <short bullet, max 12 words>

Explanation:
<2-3 sentences max. Be direct and specific.>

Safety Advice:
- <short actionable advice>
- <short actionable advice>
"""
)

risk_chain = prompt | llm
print("[ScamScope] Initialization complete.")
# ==========================================

def analyze_message(user_text):
    """Analyze the message using the globally loaded chain for instant inference."""
    docs = retriever.invoke(user_text)
    context = "\n\n".join(doc.page_content for doc in docs)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = risk_chain.invoke(
                {
                    "user_input": user_text,
                    "context": context
                }
            )
            return response.content
        except Exception as e:
            last_error = e
            error_msg = str(e)
            is_rate_limit = any(keyword in error_msg for keyword in [
                "RESOURCE_EXHAUSTED", "quota", "429", "rate limit",
                "Too Many Requests", "ResourceExhausted"
            ])
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                wait_time = INITIAL_BACKOFF * (2 ** attempt)
                print(f"[ScamScope] Rate limited. Retrying in {wait_time}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                raise last_error

    raise last_error

if __name__ == "__main__":
    print("Paste the complete email / message below and press Enter:\n")
    user_input = input().strip()
    if not user_input:
        print("No input detected. Please paste a complete message.")
        exit(1)
    print("\nAnalyzing...\n")
    result = analyze_message(user_input)
    print(result)
