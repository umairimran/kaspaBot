"""
Core functionality for Kaspa RAG system.
Consolidates embedding creation, retrieval, and data processing.
"""

import json
import re
import faiss
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tqdm import tqdm
from openai import OpenAI

from config import OPENAI_API_KEY
from pdf_processor import process_whitepaper_pdf

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


# =============================================================================
# EMBEDDING CREATION
# =============================================================================

def create_embeddings(df: pd.DataFrame, index_path: str):
    """Create and save FAISS embeddings from DataFrame."""
    vectors = []
    metadata = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        emb = client.embeddings.create(
            model="text-embedding-ada-002",
            input=row["content"]
        ).data[0].embedding
        vectors.append(emb)
        metadata.append(row.to_dict())

    # Save FAISS index
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype("float32"))
    faiss.write_index(index, index_path)

    # Save metadata
    pd.DataFrame(metadata).to_json(index_path + ".meta.json", orient="records", indent=2)
    print(f"✅ Saved index to {index_path} and metadata to {index_path}.meta.json")


# =============================================================================
# DATA PROCESSING
# =============================================================================

def load_and_chunk_kasparchive(json_path: str) -> List[Dict[str, Any]]:
    """Load and chunk KaspArchive JSON data."""
    if not Path(json_path).exists():
        return []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chunks = []
    for section in data.get("sections", []):
        section_content = []
        section_content.append(section.get("heading", ""))
        
        if section.get("false_claim"):
            section_content.append(f"False Claim: {section['false_claim']}")
        
        for fact in section.get("facts", []):
            section_content.append(f"{fact['label']}: {fact['text']}")
        
        chunks.append({
            "id": f"kasparchive_{section['label']}",
            "content": "\n".join(section_content),
            "source": "kasparchive",
            "section": section["label"],
            "url": data.get("url", "")
        })
    
    return chunks


def parse_kaspa_x_content(content: str) -> List[Dict[str, Any]]:
    """Parse Kaspa X/Twitter content into chunks."""
    lines = content.strip().split('\n')
    chunks = []
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for numbered points
        if any(line.startswith(f'{i})') for i in range(1, 11)):
            # Save previous section
            if current_section and current_content:
                chunks.append({
                    "id": f"kaspa_x_{current_section}",
                    "content": "\n".join(current_content),
                    "source": "kaspa_x_twitter",
                    "section": f"FUD {current_section}",
                    "url": "https://x.com/dotkrueger/status/1956843811679989918"
                })
            
            # Start new section
            point_num = line.split(')')[0]
            start_quote = line.find('"')
            end_quote = line.rfind('"')
            if start_quote != -1 and end_quote != -1 and end_quote > start_quote:
                claim = line[start_quote+1:end_quote]
            else:
                claim = line.split(')')[1].strip()
            
            current_section = point_num
            current_content = [f"FUD {point_num}: {claim}"]
        elif current_section:
            current_content.append(line)
    
    # Add the last section
    if current_section and current_content:
        chunks.append({
            "id": f"kaspa_x_{current_section}",
            "content": "\n".join(current_content),
            "source": "kaspa_x_twitter",
            "section": f"FUD {current_section}",
            "url": "https://x.com/dotkrueger/status/1956843811679989918"
        })
    
    return chunks


def parse_generic_text(content: str, filename: str, source_type: str = "generic") -> List[Dict[str, Any]]:
    """Parse generic text content into chunks."""
    paragraphs = content.strip().split('\n\n')
    chunks = []
    
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            chunks.append({
                "id": f"{source_type}_{filename}_{i}",
                "content": paragraph.strip(),
                "source": source_type,
                "section": f"Section {i+1}",
                "filename": filename
            })
    
    return chunks


def create_comprehensive_embeddings():
    """Create embeddings from all available content sources."""
    all_chunks = []
    
    # 1. Load existing kasparchive data
    print("📖 Loading existing kasparchive data...")
    kasparchive_chunks = load_and_chunk_kasparchive("data/kasparchive.json")
    all_chunks.extend(kasparchive_chunks)
    print(f"✅ Loaded {len(kasparchive_chunks)} chunks from kasparchive")
    
    # 2. Load and parse Kaspa X content
    kaspa_x_path = Path("/data/kaspaXcontent.txt")
    if kaspa_x_path.exists():
        print("📖 Loading Kaspa X content...")
        with open(kaspa_x_path, 'r', encoding='utf-8') as f:
            kaspa_x_content = f.read()
        
        kaspa_x_chunks = parse_kaspa_x_content(kaspa_x_content)
        all_chunks.extend(kaspa_x_chunks)
        print(f"✅ Loaded {len(kaspa_x_chunks)} chunks from Kaspa X content")
    
    # 3. Load whitepapers (text files and PDFs)
    whitepaper_dir = Path("data/whitepapers")
    if whitepaper_dir.exists():
        print("📖 Loading whitepapers...")
        
        # Process text files
        for whitepaper_file in whitepaper_dir.glob("*.txt"):
            with open(whitepaper_file, 'r', encoding='utf-8') as f:
                content = f.read()
            chunks = parse_generic_text(content, whitepaper_file.stem, "whitepaper")
            all_chunks.extend(chunks)
            print(f"✅ Loaded {len(chunks)} chunks from {whitepaper_file.name}")
        
        # Process PDF files
        for pdf_file in whitepaper_dir.glob("*.pdf"):
            try:
                print(f"📄 Processing PDF: {pdf_file.name}")
                pdf_chunks = process_whitepaper_pdf(str(pdf_file))
                all_chunks.extend(pdf_chunks)
                print(f"✅ Loaded {len(pdf_chunks)} intelligent chunks from {pdf_file.name}")
            except Exception as e:
                print(f"❌ Failed to process {pdf_file.name}: {e}")
                continue
    
    # 4. Load generic content (prioritize cleaned versions)
    generic_dir = Path("/data/generic")
    generic_cleaned_dir = Path("/data/generic_cleaned")
    
    if generic_dir.exists():
        print("📖 Loading generic content...")
        
        # Check for cleaned versions first
        if generic_cleaned_dir.exists():
            print("🧹 Using cleaned versions from generic_cleaned/")
            for text_file in generic_cleaned_dir.glob("*.txt"):
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                chunks = parse_generic_text(content, text_file.stem, "generic")
                all_chunks.extend(chunks)
                print(f"✅ Loaded {len(chunks)} chunks from cleaned {text_file.name}")
        else:
            print("📄 Using original versions from generic/ (run clean_generic_texts.py for better results)")
            # Only load .txt files directly in generic folder, exclude subdirectories
            for text_file in generic_dir.glob("*.txt"):
                if text_file.parent.name == "generic":  # Exclude files in subdirectories like kips/
                    with open(text_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    chunks = parse_generic_text(content, text_file.stem, "generic")
                    all_chunks.extend(chunks)
                    print(f"✅ Loaded {len(chunks)} chunks from {text_file.name}")
                else:
                    print(f"⏭️  Skipping {text_file.name} (in subfolder - run clean_generic_texts.py to include)")
    
    if not all_chunks:
        print("❌ No content found to embed!")
        return
    
    # Convert to DataFrame and create embeddings
    df = pd.DataFrame(all_chunks)
    print(f"🔍 Creating embeddings for {len(df)} chunks...")
    
    index_path = "embeddings/vector_index_flexible.faiss"
    create_embeddings(df, index_path)
    
    print(f"✅ Embeddings created successfully!")
    print(f"📁 Index saved to: {index_path}")
    print(f"📁 Metadata saved to: {index_path}.meta.json")
    print(f"📊 Total chunks: {len(df)}")
    print(f"📊 Sources: {df['source'].value_counts().to_dict()}")


# =============================================================================
# RETRIEVAL
# =============================================================================

def load_index(index_path: str) -> Tuple[faiss.Index, pd.DataFrame]:
    """Load FAISS index and metadata."""
    index = faiss.read_index(index_path)
    metadata = pd.read_json(index_path + ".meta.json")
    return index, metadata


def retrieve(query: str, index: faiss.Index, metadata: pd.DataFrame, k: int = 8) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks using semantic search with technical prioritization."""
    # Create query embedding
    query_embedding = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    ).data[0].embedding
    
    # Search with more results to allow for filtering
    search_k = min(k * 4, len(metadata))  # Get 4x more results for filtering
    query_vector = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(query_vector, search_k)
    
    # Collect all results with enhanced scoring
    candidate_results = []
    
    # Technical term lists for better matching
    protocol_terms = ['knight', 'k-colouring', 'umc-voting', 'ghostdag', 'phantom', 'algorithm', 'procedure']
    mechanism_terms = ['tie-breaking', 'consensus', 'safety', 'liveness', 'cluster', 'excessive rank', 'natural rank']
    precision_terms = ['returns', 'ensures', 'prevents', 'selects', 'validates', 'determines']
    
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            row = metadata.iloc[idx]
            base_score = 1 / (1 + distances[0][i])  # Convert distance to similarity score
            
            query_lower = query.lower()
            content_lower = row["content"].lower()
            
            # Enhanced scoring based on feedback requirements
            boost = 1.0
            
            # Boost for technical content that mentions specific procedures
            if any(term in content_lower for term in protocol_terms):
                boost *= 1.6
                
            # Additional boost for mechanism descriptions
            if any(term in content_lower for term in mechanism_terms):
                boost *= 1.4
                
            # Boost for precise language (indicates exact procedures)
            if any(term in content_lower for term in precision_terms):
                boost *= 1.3
            
            # Prioritize whitepaper content for technical queries
            if row["source"] == "whitepaper":
                boost *= 1.5
                
            # Extra boost for KNIGHT-specific content
            if 'knight' in query_lower and 'knight' in content_lower:
                boost *= 1.8
                
            # Boost for safety/liveness distinction content
            if any(term in query_lower for term in ['safety', 'liveness']) and any(term in content_lower for term in ['safety', 'liveness']):
                boost *= 1.7
            
            final_score = base_score * boost
            
            candidate_results.append({
                "content": row["content"],
                "source": row["source"],
                "section": row["section"],
                "id": row["id"],
                "distance": float(distances[0][i]),
                "score": final_score,
                "url": row.get("url", ""),
                "filename": row.get("filename", "")
            })
    
    # Sort by enhanced score and return top k
    candidate_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Remove score from final results and return top k
    results = []
    for result in candidate_results[:k]:
        result_copy = result.copy()
        result_copy.pop("score", None)
        results.append(result_copy)
    
    return results


def build_prompt(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build prompt for LLM with retrieved context, optimized for technical precision."""
    # Organize context by relevance and source type
    context_parts = []
    
    # Prioritize whitepaper content first for technical accuracy
    whitepaper_results = [r for r in results if r['source'] == 'whitepaper']
    other_results = [r for r in results if r['source'] != 'whitepaper']
    
    # Combine in priority order
    prioritized_results = whitepaper_results + other_results
    
    for result in prioritized_results:
        # Create concise source identifier
        source_tag = f"[{result['source'].upper()}"
        if result.get('filename'):
            source_tag += f":{result['filename']}"
        if result.get('section'):
            source_tag += f":{result['section']}"
        source_tag += "]"
        
        context_parts.append(f"{source_tag}\n{result['content']}\n")
    
    context = "\n".join(context_parts)
    
    system_prompt = """You are KaspaBot — a specialized technical expert exclusively focused on Kaspa cryptocurrency and blockchain protocols.

SCOPE & CONTEXT INTELLIGENCE:
- You ONLY have knowledge about Kaspa blockchain, cryptocurrency, protocols, and ecosystem
- For ANY question, first determine if it relates to Kaspa (even if not explicitly mentioned) but don't write something like I am assuming your question is on kaspa. Just start the answer.
- Common implicit Kaspa contexts: "team", "mining", "premine", "tokens", "consensus", "DAG", "blockchain", "cryptocurrency"
- If a question seems unrelated to Kaspa, respond: "I specialize exclusively in Kaspa cryptocurrency and blockchain technology. Could you clarify how your question relates to Kaspa, or ask me something about Kaspa protocols, mining, development, or ecosystem?"

QUESTION INTERPRETATION:
- Examples:
  * "Did the team premine?" → Interpret as "Did the Kaspa team premine?"
  * "What's the consensus algorithm?" → Interpret as "What's Kaspa's consensus algorithm?"
  * "How does mining work?" → Interpret as "How does Kaspa mining work?"
- For unclear questions, provide both clarification and a Kaspa-focused answer
- Example: "I'll answer assuming you're asking about Kaspa. [Answer]. If you meant something else, please specify."

TECHNICAL PRECISION REQUIREMENTS:
1) EXACT PROCEDURE NAMES: Never use generic terms. Always name specific algorithms and procedures.
   - Use "K-Colouring procedure" and "UMC-Voting procedure", not "Algorithm 3/4"
   - State what each procedure returns: "K-Colouring returns a valid k-colouring of blocks"
   - Use exact function names from the source material

2) SAFETY vs LIVENESS DISTINCTION: Be precise about different failure modes.
   - Safety violations: incorrect/invalid outcomes that break protocol rules
   - Liveness violations: delayed but eventually correct outcomes
   - Never confuse these concepts or use them interchangeably

3) MECHANISM-FOCUSED EXPLANATIONS: Explain HOW things work, not just what they do.
   - For tie-breaking: "KNIGHT selects the tip whose cluster least recently used an excessive rank"
   - Include the specific rule or condition that triggers each action
   - State exact parameters, thresholds, and decision criteria

4) CUT VAGUE LANGUAGE: Eliminate imprecise phrases.
   - Replace "helps ensure" with "ensures" or "prevents"
   - Replace "generally" or "typically" with specific conditions
   - Remove hedging language when the mechanism is deterministic

5) SOURCE GROUNDING: Use only terminology and facts from the provided context.
   - Quote exact parameter names and values when available
   - Reference specific protocol rules and constraints
   - Use the precise technical vocabulary from the papers

6) CONCISE ANSWERS: Be direct and focused.
   - Lead with the specific mechanism or procedure name
   - State what it does and how it works
   - Avoid unnecessary background or context unless directly relevant

7) INCLUDE SOURCES: Always include a "Sources:" section at the end listing the relevant sources used.
   - Format: "Sources: [SOURCE_TYPE:filename/section]"
   - Example: "Sources: [WHITEPAPER:KNIGHT_Protocol], [GENERIC:Kaspa_101]"

Answer with technical precision using exact terminology, followed by source attribution."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Technical Context:\n{context}\n\nQuestion: {query}\n\nProvide a precise, mechanism-focused answer about Kaspa using exact procedure names and terminology from the context. If the question doesn't explicitly mention Kaspa but seems related to cryptocurrency/blockchain, assume it's about Kaspa and clarify your interpretation."}
    ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_flexible_index(index_path: str) -> Tuple[faiss.Index, pd.DataFrame]:
    """Alias for load_index for backward compatibility."""
    return load_index(index_path)


def retrieve_flexible(query: str, index: faiss.Index, metadata: pd.DataFrame, k: int = 5) -> List[Dict[str, Any]]:
    """Alias for retrieve for backward compatibility."""
    return retrieve(query, index, metadata, k)


def build_flexible_prompt(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Alias for build_prompt for backward compatibility."""
    return build_prompt(query, results)


if __name__ == "__main__":
    create_comprehensive_embeddings()