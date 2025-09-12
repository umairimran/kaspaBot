# Qdrant DB utility for embeddings
# Install qdrant-client: pip install qdrant-client

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import numpy as np
import os

# Allow overriding via environment for containerized deployments
# Defaults keep local dev working out of the box
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6333'))
COLLECTION_NAME = 'kaspa_embeddings'
VECTOR_SIZE = 1536  # Change to your embedding size

# Initialize client with error handling
try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    # Test connection
    client.get_collections()
    print(f"✅ Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
except Exception as e:
    print(f"❌ Failed to connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}: {e}")
    client = None

def create_collection():
    if not client:
        raise Exception("Qdrant client not connected")
    
    if COLLECTION_NAME not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"✅ Created collection '{COLLECTION_NAME}'")
    else:
        print(f"✅ Collection '{COLLECTION_NAME}' already exists")

def upsert_embedding(id: int, embedding: np.ndarray, payload: dict = None):
    if not client:
        raise Exception("Qdrant client not connected")
        
    point = PointStruct(
        id=id,
        vector=embedding.tolist(),
        payload=payload or {}
    )
    client.upsert(collection_name=COLLECTION_NAME, points=[point])

def search_embedding(query_embedding: np.ndarray, top_k: int = 5):
    if not client:
        raise Exception("Qdrant client not connected")
        
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=top_k
    )
    return results

def get_collection_info():
    """Get information about the collection."""
    if not client:
        return {"error": "Qdrant client not connected", "status": "disconnected"}
    
    try:
        info = client.get_collection(COLLECTION_NAME)
        return {
            "points_count": info.points_count,
            "vector_size": info.config.params.vectors.size,
            "status": "connected"
        }
    except Exception as e:
        print(f"Collection doesn't exist: {e}")
        return {"error": str(e), "status": "collection_not_found"}

def count_points():
    """Count total points in the collection."""
    if not client:
        return 0
        
    try:
        info = client.get_collection(COLLECTION_NAME)
        return info.points_count
    except Exception as e:
        print(f"Error counting points: {e}")
        return 0

def migrate_embeddings_from_faiss():
    """Migrate existing FAISS embeddings to Qdrant"""
    import faiss
    import pandas as pd
    from pathlib import Path
    
    # Paths to existing embeddings
    index_path = "../../embeddings/vector_index_flexible.faiss"
    metadata_path = "../../embeddings/vector_index_flexible.faiss.meta.json"
    
    if not Path(index_path).exists():
        print(f"❌ FAISS index not found at {index_path}")
        return
    
    if not Path(metadata_path).exists():
        print(f"❌ Metadata not found at {metadata_path}")
        return
    
    print("📥 Loading FAISS embeddings...")
    # Load FAISS index and metadata
    index = faiss.read_index(index_path)
    metadata = pd.read_json(metadata_path)
    
    # Create Qdrant collection
    print("🏗️ Creating Qdrant collection...")
    create_collection()
    
    # Extract vectors from FAISS
    vectors = []
    for i in range(index.ntotal):
        vector = index.reconstruct(i)
        vectors.append(vector)
    
    print(f"🔄 Migrating {len(vectors)} embeddings to Qdrant...")
    
    # Upsert to Qdrant
    for i, (vector, meta_row) in enumerate(zip(vectors, metadata.iterrows())):
        _, meta_data = meta_row
        payload = meta_data.to_dict()
        upsert_embedding(i, vector, payload)
        
        if (i + 1) % 100 == 0:
            print(f"   ✅ Migrated {i + 1}/{len(vectors)} embeddings")
    
    print(f"🎉 Successfully migrated {len(vectors)} embeddings to Qdrant!")
    return len(vectors)

if __name__ == "__main__":
    import numpy as np
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        # Migrate existing embeddings from FAISS to Qdrant
        migrate_embeddings_from_faiss()
    else:
        print("🚀 Testing Qdrant connection...")
        
        # 1. Create the collection
        print("📁 Creating collection...")
        create_collection()
        print("✅ Collection created/verified")
        
        # 2. Add some test embeddings
        print("📊 Adding test embeddings...")
        for i in range(3):
            emb = np.random.rand(VECTOR_SIZE).astype(np.float32)
            payload = {"text": f"test document {i+1}", "source": "test"}
            upsert_embedding(i+1, emb, payload)
        print("✅ Test embeddings added")
        
        # 3. Search for similar embeddings
        print("🔍 Testing search...")
        query_emb = np.random.rand(VECTOR_SIZE).astype(np.float32)
        results = search_embedding(query_emb, top_k=3)
        
        print(f"📈 Found {len(results)} results:")
        for hit in results:
            print(f"  ID: {hit.id}, Score: {hit.score:.4f}, Payload: {hit.payload}")
        
        # 4. Show collection info
        print("\n📊 Collection Info:")
        info = get_collection_info()
        if info:
            print(f"  Points count: {info.points_count}")
            print(f"  Vector size: {info.config.params.vectors.size}")
        
        print("\n🎉 Qdrant is working correctly!")
        print("\n💡 To migrate your real embeddings, run: python qdrant_utils.py migrate")
