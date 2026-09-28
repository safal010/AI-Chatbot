from vector_store import load_vector_store, search_documents
from gemini import ask_gemini, client


def ask_rag_stream(question: str, conversation: str = ""):
    # Load the vector store
    load_vector_store()

    # Retrieve relevant website information
    documents = search_documents(
        question,
        number_of_results=3
    )

    # If nothing was found
    if not documents:
        yield "I could not find relevant information in the knowledge base."
        return

    # Combine retrieved documents
    context = "\n\n".join(documents)

    # Create the RAG prompt
    prompt = f"""
You are an AI assistant for Insyde AI.

Answer the user's question using ONLY the information provided
in the knowledge base context below.

You may also use the conversation history to understand
what the user is referring to.

If the answer is not available in the knowledge base, say:
"I don't have that information in the Insyde AI knowledge base."

Do not make up information.

When answering, summarize the relevant information in your own words.
Do not copy quotation marks, quoted example questions, or special characters
from the knowledge base unless they are necessary to answer the question.

Knowledge base context:
{context}

Conversation history:
{conversation}

Current user question:
{question}
"""

    print("\nSending context and conversation to Gemini...")

    response = client.models.generate_content_stream(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text


def ask_rag(question: str, conversation: str = ""):
    # Load the vector store
    load_vector_store()

    # Retrieve relevant website information
    documents = search_documents(
        question,
        number_of_results=3
    )

    # If nothing was found
    if not documents:
        return "I could not find relevant information in the knowledge base."

    # Combine retrieved documents
    context = "\n\n".join(documents)

    # Create the RAG prompt
    prompt = f"""
You are an AI assistant for Insyde AI.

Answer the user's question using ONLY the information provided
in the knowledge base context below.

You may also use the conversation history to understand
what the user is referring to.

If the answer is not available in the knowledge base, say:
"I don't have that information in the Insyde AI knowledge base."

Do not make up information.

When answering, summarize the relevant information in your own words.
Do not copy quotation marks, quoted example questions, or special characters
from the knowledge base unless they are necessary to answer the question.

Knowledge base context:
{context}

Conversation history:
{conversation}

Current user question:
{question}
"""

    print("\nSending context and conversation to Gemini...")

    answer = ask_gemini(prompt)

    print("Gemini response received.")

    return answer


if __name__ == "__main__":
    question = "What services does Insyde AI provide?"

    answer = ask_rag(question)

    print("\nRAG Answer:")
    print(answer)