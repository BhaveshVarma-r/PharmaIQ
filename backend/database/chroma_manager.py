import chromadb
import logging

logger = logging.getLogger(__name__)

CHROMA_PATH = "./chroma_db"
_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def get_or_create_collection(name):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def query_collection(collection_name, query_text, n_results=3):
    try:
        collection = get_or_create_collection(collection_name)
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, count)
        )
        if not results["documents"] or not results["documents"][0]:
            return []
        docs = []
        for i, doc in enumerate(results["documents"][0]):
            docs.append({
                "content": doc,
                "metadata": (
                    results["metadatas"][0][i] if results["metadatas"] else {}
                ),
                "distance": (
                    results["distances"][0][i] if results["distances"] else 1.0
                ),
            })
        return docs
    except Exception as e:
        logger.error(
            "ChromaDB query error [{}]: {}".format(collection_name, e)
        )
        return []


def add_documents(collection_name, documents, metadatas, ids):
    collection = get_or_create_collection(collection_name)
    try:
        existing = collection.get(ids=ids)
        existing_ids = set(existing["ids"])
    except Exception:
        existing_ids = set()

    new_docs = []
    new_metas = []
    new_ids = []
    for doc, meta, id_ in zip(documents, metadatas, ids):
        if id_ not in existing_ids:
            new_docs.append(doc)
            new_metas.append(meta)
            new_ids.append(id_)

    if new_docs:
        collection.add(
            documents=new_docs,
            metadatas=new_metas,
            ids=new_ids
        )
        logger.info(
            "Added {} documents to {}".format(len(new_docs), collection_name)
        )
    else:
        logger.info(
            "All documents already exist in {}".format(collection_name)
        )