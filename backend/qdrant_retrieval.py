"""
Qdrant-based retrieval functions for the backend
"""
import sys
sys.path.append('db')

from db.qdrant_utils import client, COLLECTION_NAME, search_embedding, get_collection_info
from openai import OpenAI
from config import OPENAI_API_KEY
import numpy as np
from typing import List, Dict, Any

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def retrieve_from_qdrant(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks from Qdrant using semantic search."""
    
    # Create query embedding
    query_embedding = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    ).data[0].embedding
    
    # Search in Qdrant
    results = search_embedding(np.array(query_embedding), top_k=k)
    
    # Convert to expected format
    formatted_results = []
    for hit in results:
        result = {
            "content": hit.payload.get("content", ""),
            "source": hit.payload.get("source", ""),
            "section": hit.payload.get("section", ""),
            "filename": hit.payload.get("filename", ""),
            "url": hit.payload.get("url", ""),
            "score": hit.score
        }
        formatted_results.append(result)
    
    return formatted_results

def add_new_embedding_to_qdrant(content: str, metadata: Dict[str, Any]) -> bool:
    """Add a new embedding to Qdrant collection."""
    if not client:
        print("❌ Qdrant client not connected")
        return False
        
    try:
        # Create embedding for the new content
        embedding = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=content
        ).data[0].embedding
        
        # Get next available ID
        collection_info = get_collection_info()
        if collection_info.get("status") != "connected":
            print(f"❌ Collection not available: {collection_info}")
            return False
            
        next_id = collection_info.get("points_count", 0)
        
        # Add content to metadata
        full_metadata = {
            "content": content,
            **metadata
        }
        
        # Import upsert function
        from db.qdrant_utils import upsert_embedding
        
        # Add to Qdrant
        upsert_embedding(next_id, np.array(embedding), full_metadata)
        
        print(f"✅ Added new embedding with ID {next_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding embedding: {e}")
        return False

def bulk_add_embeddings_to_qdrant(documents: List[Dict[str, Any]]) -> int:
    """Add multiple new embeddings to Qdrant."""
    added_count = 0
    
    for doc in documents:
        content = doc.get("content", "")
        metadata = {k: v for k, v in doc.items() if k != "content"}
        
        if add_new_embedding_to_qdrant(content, metadata):
            added_count += 1
    
    print(f"✅ Added {added_count}/{len(documents)} new embeddings")
    return added_count

def get_qdrant_collection_info():
    """Get information about the Qdrant collection."""
    return get_collection_info()
