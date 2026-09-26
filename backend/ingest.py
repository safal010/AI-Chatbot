from scraper import scrape_website
from chunker import create_chunks
from vector_store import add_document, clear_vector_store


def ingest_website():
    print("Clearing old vector store...")

    clear_vector_store()

    print("\nScraping Insyde AI website...")

    text = scrape_website()

    print("\nWebsite characters:", len(text))

    print("\nCreating chunks...")

    chunks = create_chunks(
        text,
        chunk_size=1000,
        overlap=200
    )

    print("Number of chunks:", len(chunks))

    print("\nAdding chunks to vector store...")

    for i, chunk in enumerate(chunks):
        print(f"Adding chunk {i + 1}/{len(chunks)}")

        add_document(chunk)

    print("\nIngestion completed successfully!")


if __name__ == "__main__":
    ingest_website()