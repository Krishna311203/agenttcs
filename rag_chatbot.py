import os
from dotenv import load_dotenv

from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

# ============================================================
# Validate Environment Variables
# ============================================================

required_vars = {
    "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
    "AZURE_OPENAI_KEY": AZURE_OPENAI_KEY,
    "CHAT_MODEL": CHAT_MODEL,
    "EMBEDDING_MODEL": EMBEDDING_MODEL,
    "SEARCH_ENDPOINT": SEARCH_ENDPOINT,
    "SEARCH_KEY": SEARCH_KEY,
    "INDEX_NAME": INDEX_NAME,
}

missing = [k for k, v in required_vars.items() if not v]

if missing:
    raise ValueError(
        f"Missing environment variables: {', '.join(missing)}"
    )

# ============================================================
# Azure OpenAI Client
# ============================================================

aoai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-10-21"
)

# ============================================================
# Azure AI Search Client
# ============================================================

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY)
)

# ============================================================
# Generate Embedding
# ============================================================

def generate_embedding(text: str) -> list:
    """
    Generate embeddings using Azure OpenAI.
    """

    response = aoai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding


# ============================================================
# Retrieve Relevant Documents
# ============================================================

def retrieve_documents(question: str, k: int = 5):
    """
    Perform vector search in Azure AI Search.
    """

    query_vector = generate_embedding(question)

    results = search_client.search(
        search_text=None,
        vector_queries=[
            VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=k,
                fields="text_vector"
            )
        ],
        select=[
            "chunk",
            "title",
            "parent_id"
        ]
    )

    documents = []

    for result in results:
        documents.append({
            "content": result.get("chunk", ""),
            "source": result.get(
                "title",
                "Unknown"
            )
        })

    return documents


# ============================================================
# Build Context
# ============================================================

def build_context(documents):
    """
    Convert retrieved chunks into prompt context.
    """

    context_parts = []

    for idx, doc in enumerate(documents, start=1):

        context_parts.append(
            f"""
Document {idx}
Source: {doc['source']}

Content:
{doc['content']}
"""
        )

    return "\n".join(context_parts)


# ============================================================
# Generate Answer
# ============================================================

def ask_rag(question: str) -> str:
    """
    Complete RAG flow.
    """

    documents = retrieve_documents(question)

    if not documents:
        return "No relevant documents were found."

    context = build_context(documents)

    system_prompt = """
You are a helpful enterprise assistant.

Rules:
1. Answer only from the provided context.
2. Do not make up information.
3. If the answer is not present in the context, say:
   'I could not find that information in the documents.'
4. Mention source document names whenever possible.
"""

    user_prompt = f"""
Context:
{context}

Question:
{question}
"""

    response = aoai_client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.choices[0].message.content


# ============================================================
# Interactive Chat
# ============================================================

def main():

    print("=" * 60)
    print("Azure RAG Chatbot")
    print("Type 'exit' to quit")
    print("=" * 60)

    while True:

        question = input("\nYou: ").strip()

        if not question:
            continue

        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        try:
            answer = ask_rag(question)

            print("\nBot:")
            print(answer)

        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()