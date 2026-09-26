import faiss
import numpy as np
import json
import os

from embeddings import create_embedding


INDEX_FILE = "insyde.index"
DOCUMENTS_FILE = "documents.json"


index = None
documents = []


def load_vector_store():
    global index
    global documents

    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)

    if os.path.exists(DOCUMENTS_FILE):
        with open(DOCUMENTS_FILE, "r", encoding="utf-8") as file:
            documents = json.load(file)


def save_vector_store():
    if index is not None:
        faiss.write_index(index, INDEX_FILE)

    with open(DOCUMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2
        )


def add_document(text):
    global index

    embedding = create_embedding(text)

    vector = np.array(
        [embedding],
        dtype="float32"
    )

    if index is None:
        dimension = len(embedding)
        index = faiss.IndexFlatL2(dimension)

    index.add(vector)

    documents.append(text)

    save_vector_store()


def search_documents(query, number_of_results=3):
    if index is None or index.ntotal == 0:
        return []

    query_embedding = create_embedding(query)

    query_vector = np.array(
        [query_embedding],
        dtype="float32"
    )

    number_of_results = min(
        number_of_results,
        index.ntotal
    )

    distances, indexes = index.search(
        query_vector,
        number_of_results
    )

    results = []

    for i in indexes[0]:
        if i != -1:
            results.append(documents[i])

    return results


def clear_vector_store():
    global index
    global documents

    index = None
    documents = []

    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)

    if os.path.exists(DOCUMENTS_FILE):
        os.remove(DOCUMENTS_FILE)

    print("Vector store cleared.")


if __name__ == "__main__":
    load_vector_store()

    print("Loaded documents:", len(documents))

    results = search_documents(
        "What services does Insyde AI provide?"
    )

    print("\nSearch results:")

    for i, result in enumerate(results, start=1):
        print(f"\n--- Result {i} ---")
        print(result)