import re


def create_chunks(text, chunk_size=1000, overlap=200):
    chunks = []

    # Clean extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split text into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    current_chunk = ""

    for sentence in sentences:

        # If adding the sentence stays within the chunk size
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += sentence + " "

        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Keep some text from the previous chunk
            overlap_text = current_chunk[-overlap:]

            current_chunk = overlap_text + " " + sentence + " "

    # Add the final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


if __name__ == "__main__":
    sample_text = (
        "Insyde AI provides enterprise AI solutions. "
        "It offers AI agents for businesses. "
        "These agents can work with company knowledge and documents. "
        "Insyde AI also provides CRM integrations. "
        "The platform supports secure enterprise AI."
    ) * 20

    chunks = create_chunks(sample_text)

    print("Number of chunks:", len(chunks))

    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i + 1} ---")
        print(chunk)