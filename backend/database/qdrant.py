"""
Qdrant Vector Database Service — RAG Pipeline for PDF-based Chat
═════════════════════════════════════════════════════════════════════════════
Uses:
  - Qdrant Cloud for vector storage (collection: skip_hackathon)
  - Jina Embeddings API for dense vector generation
  - Hybrid search via Query Points (dense + sparse BM25-style)
"""
import os
import re
import uuid
import math
import hashlib
from collections import Counter
from typing import List, Dict, Optional, Tuple

import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    SparseIndexParams,
    NamedVector,
    NamedSparseVector,
    SearchParams,
    Prefetch,
    Query,
    FusionQuery,
    Fusion,
)
from dotenv import load_dotenv

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

COLLECTION_NAME = "skip_hackathon"
DENSE_VECTOR_SIZE = 768  # Jina embeddings v3 output dimension
CHUNK_SIZE = 512          # Characters per chunk
CHUNK_OVERLAP = 64        # Overlap between chunks


# ═════════════════════════════════════════════════════════════════════════════
# JINA EMBEDDINGS CLIENT
# ═════════════════════════════════════════════════════════════════════════════

class JinaEmbeddings:
    """Generate dense embeddings using Jina Embeddings API v2."""

    API_URL = "https://api.jina.ai/v1/embeddings"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or JINA_API_KEY
        if not self.api_key:
            raise RuntimeError("JINA_API_KEY is not set")

    def embed(self, texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
        """
        Get embeddings for a list of texts.
        task: 'retrieval.passage' for documents, 'retrieval.query' for queries.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "jina-embeddings-v3",
            "task": task,
            "dimensions": DENSE_VECTOR_SIZE,
            "late_chunking": False,
            "input": texts,
        }

        try:
            with httpx.Client(timeout=120) as client:  # Increased timeout to 120s
                resp = client.post(self.API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            print(f"   ❌ [Jina] HTTP Error {e.response.status_code}: {e.response.text}")
            raise RuntimeError(f"Jina API error: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException as e:
            print(f"   ❌ [Jina] Request timeout after 120s. API may be slow or overloaded.")
            raise RuntimeError(f"Jina API timeout: {str(e)}")
        except Exception as e:
            print(f"   ❌ [Jina] Embedding failed: {type(e).__name__}: {str(e)}")
            raise RuntimeError(f"Jina embedding error: {str(e)}")

        embeddings = [item["embedding"] for item in data["data"]]
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string (uses retrieval.query task)."""
        return self.embed([query], task="retrieval.query")[0]

    def embed_documents(self, docs: List[str]) -> List[List[float]]:
        """Embed multiple document chunks (uses retrieval.passage task)."""
        # Batch in groups of 64 (Jina API limit)
        all_embeddings = []
        total_batches = (len(docs) + 63) // 64
        
        for batch_idx, i in enumerate(range(0, len(docs), 64)):
            batch = docs[i : i + 64]
            try:
                print(f"   📊 [Jina] Batch {batch_idx + 1}/{total_batches}: embedding {len(batch)} chunks...")
                embeddings = self.embed(batch, task="retrieval.passage")
                all_embeddings.extend(embeddings)
            except Exception as e:
                print(f"   ❌ [Jina] Batch {batch_idx + 1} failed: {e}")
                raise
        
        return all_embeddings


# ═════════════════════════════════════════════════════════════════════════════
# SPARSE (BM25-STYLE) VECTOR GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

class SparseBM25:
    """
    Simple BM25-inspired sparse vector generator.
    Converts text into sparse TF-IDF-like vectors for hybrid search.
    """

    STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "be", "been",
        "has", "have", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "this", "that", "these", "those",
        "it", "its", "he", "she", "they", "we", "you", "i", "me", "my",
        "your", "his", "her", "our", "their", "what", "which", "who",
        "where", "when", "why", "how", "if", "about", "up", "out", "not",
        "so", "no", "just", "than", "then", "also", "very", "too", "each",
        "much", "more", "most", "some", "any", "all",
    }

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Lowercase, strip punctuation, remove stop words."""
        text = text.lower()
        tokens = re.findall(r"\b[a-z0-9]+\b", text)
        return [t for t in tokens if t not in SparseBM25.STOP_WORDS and len(t) > 1]

    @staticmethod
    def text_to_sparse(text: str) -> SparseVector:
        """
        Convert text to a BM25-style sparse vector.
        Uses hashed token IDs as indices and TF-IDF-like values.
        """
        tokens = SparseBM25.tokenize(text)
        if not tokens:
            return SparseVector(indices=[0], values=[0.0])

        tf = Counter(tokens)
        max_tf = max(tf.values())

        indices = []
        values = []

        for token, count in tf.items():
            # Hash token to get a stable integer index
            idx = int(hashlib.md5(token.encode()).hexdigest()[:8], 16) % (2**31)
            # Augmented TF: 0.5 + 0.5 * (count / max_count)
            score = 0.5 + 0.5 * (count / max_tf)
            indices.append(idx)
            values.append(round(score, 4))

        return SparseVector(indices=indices, values=values)


# ═════════════════════════════════════════════════════════════════════════════
# TEXT CHUNKING — Using LangChain RecursiveCharacterTextSplitter
# ═════════════════════════════════════════════════════════════════════════════

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks using LangChain's RecursiveCharacterTextSplitter.
    Intelligently splits by multiple separators (paragraphs, sentences, words).
    
    Args:
        text: Input text to split
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],  # Splits by paragraph, line, sentence, word, char
    )
    chunks = splitter.split_text(text)
    return chunks if chunks else []


# ═════════════════════════════════════════════════════════════════════════════
# QDRANT RAG SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class QdrantRAGService:
    """
    Full RAG service: PDF ingestion → Qdrant storage → Hybrid search → Context retrieval.
    Uses hybrid search with Query Points (dense + sparse fusion).
    """

    def __init__(self):
        if not QDRANT_URL or not QDRANT_KEY:
            raise RuntimeError("QDRANT_URL / QDRANT_KEY not set in environment")

        self.client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_KEY,
            timeout=60,  # Increased timeout to 60s
            grpc_options={"grpc.max_receive_message_length": 10 * 1024 * 1024},  # 10MB max
        )
        self.embedder = JinaEmbeddings()
        self.sparse = SparseBM25()
        self._ensure_collection()

    def _ensure_collection(self):
        """Create the skip_hackathon collection if it doesn't exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            print(f"📦 [Qdrant] Creating collection '{COLLECTION_NAME}'...")
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "dense": VectorParams(
                        size=DENSE_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(on_disk=False),
                    ),
                },
            )
            print(f"✅ [Qdrant] Collection '{COLLECTION_NAME}' created successfully")
        else:
            print(f"✅ [Qdrant] Collection '{COLLECTION_NAME}' already exists")

    # ─────────────────────────────────────────────────────────────────────
    # INGEST: PDF text → chunks → vectors → Qdrant
    # ─────────────────────────────────────────────────────────────────────
    def ingest_document(
        self,
        text: str,
        chat_id: str,
        user_id: str,
        filename: str,
        pdf_id: str = None,
    ) -> Dict:
        """
        Ingest extracted PDF text into Qdrant.
        Returns ingestion stats.
        """
        pdf_id = pdf_id or str(uuid.uuid4())

        print(f"\n📥 [Qdrant] Ingesting document: {filename}")
        print(f"   📄 Text length: {len(text)} chars")

        # 1. Chunk the text
        chunks = chunk_text(text)
        if not chunks:
            return {"status": "empty", "chunks": 0, "pdf_id": pdf_id}

        print(f"   🔪 Chunked into {len(chunks)} segments")

        # 2. Generate dense embeddings
        print(f"   🧮 Generating Jina embeddings...")
        dense_vectors = self.embedder.embed_documents(chunks)
        print(f"   ✅ Generated {len(dense_vectors)} dense vectors")

        # 3. Generate sparse vectors
        sparse_vectors = [self.sparse.text_to_sparse(chunk) for chunk in chunks]

        # 4. Build points
        points = []
        for i, (chunk, dense_vec, sparse_vec) in enumerate(
            zip(chunks, dense_vectors, sparse_vectors)
        ):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_vec,
                        "sparse": sparse_vec,
                    },
                    payload={
                        "text": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "filename": filename,
                        "pdf_id": pdf_id,
                        "chat_id": chat_id,
                        "user_id": user_id,
                    },
                )
            )

        # 5. Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
            )
            print(f"   💾 Uploaded batch {i // batch_size + 1}/{math.ceil(len(points) / batch_size)}")

        print(f"   ✅ [Qdrant] Ingestion complete — {len(points)} vectors stored")

        return {
            "status": "success",
            "pdf_id": pdf_id,
            "chunks": len(chunks),
            "filename": filename,
        }

    # ─────────────────────────────────────────────────────────────────────
    # HYBRID SEARCH: Query Points (dense + sparse + RRF fusion)
    # ─────────────────────────────────────────────────────────────────────
    def hybrid_search(
        self,
        query: str,
        chat_id: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Hybrid search using Qdrant Query Points API.
        Combines dense (Jina) + sparse (BM25) with Reciprocal Rank Fusion.
        Filters results to the specific chat's PDFs.
        """
        print(f"\n🔍 [Qdrant] Hybrid search: '{query[:80]}...'")

        # 1. Get query embeddings
        dense_query = self.embedder.embed_query(query)
        sparse_query = self.sparse.text_to_sparse(query)

        # 2. Use Query Points with prefetch + fusion
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        chat_filter = Filter(
            must=[
                FieldCondition(key="chat_id", match=MatchValue(value=chat_id)),
            ]
        )

        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=[
                Prefetch(
                    query=dense_query,
                    using="dense",
                    limit=top_k * 2,
                    filter=chat_filter,
                ),
                Prefetch(
                    query=sparse_query,
                    using="sparse",
                    limit=top_k * 2,
                    filter=chat_filter,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
        )

        # 3. Format results
        search_results = []
        for point in results.points:
            search_results.append({
                "text": point.payload.get("text", ""),
                "score": point.score,
                "chunk_index": point.payload.get("chunk_index"),
                "filename": point.payload.get("filename"),
                "pdf_id": point.payload.get("pdf_id"),
            })

        print(f"   ✅ [Qdrant] Found {len(search_results)} results")
        for i, r in enumerate(search_results):
            print(f"      [{i+1}] score={r['score']:.4f} | chunk={r['chunk_index']} | file={r['filename']}")

        return search_results

    # ─────────────────────────────────────────────────────────────────────
    # BUILD RAG CONTEXT: Search → Format for LLM
    # ─────────────────────────────────────────────────────────────────────
    def get_rag_context(
        self,
        query: str,
        chat_id: str,
        top_k: int = 5,
    ) -> Optional[str]:
        """
        Search for relevant PDF context and format it for the LLM.
        Returns formatted context string or None if no relevant docs found.
        """
        results = self.hybrid_search(query, chat_id, top_k=top_k)
        if not results:
            return None

        # Build context block
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[Source {i} — {r['filename']}, chunk {r['chunk_index']}]\n{r['text']}"
            )

        context = "\n\n---\n\n".join(context_parts)
        return context

    # ─────────────────────────────────────────────────────────────────────
    # DELETE: Remove all vectors for a specific PDF or chat
    # ─────────────────────────────────────────────────────────────────────
    def delete_pdf_vectors(self, pdf_id: str) -> int:
        """Delete all vectors associated with a specific PDF."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        result = self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(key="pdf_id", match=MatchValue(value=pdf_id)),
                ]
            ),
        )
        print(f"🗑️ [Qdrant] Deleted vectors for pdf_id={pdf_id}")
        return result

    def delete_chat_vectors(self, chat_id: str) -> int:
        """Delete all vectors associated with a specific chat."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        result = self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(key="chat_id", match=MatchValue(value=chat_id)),
                ]
            ),
        )
        print(f"🗑️ [Qdrant] Deleted all vectors for chat_id={chat_id}")
        return result

    def get_chat_pdfs(self, chat_id: str) -> List[Dict]:
        """Get list of PDFs uploaded to a specific chat."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Scroll through to find unique PDFs
        results, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="chat_id", match=MatchValue(value=chat_id)),
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        # Deduplicate by pdf_id
        seen = {}
        for point in results:
            pid = point.payload.get("pdf_id")
            if pid and pid not in seen:
                seen[pid] = {
                    "pdf_id": pid,
                    "filename": point.payload.get("filename", "unknown"),
                    "total_chunks": point.payload.get("total_chunks", 0),
                }

        return list(seen.values())


# ═════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE (lazy init)
# ═════════════════════════════════════════════════════════════════════════════
_rag_service: Optional[QdrantRAGService] = None


def get_rag_service() -> QdrantRAGService:
    """Get or create the singleton RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = QdrantRAGService()
    return _rag_service
