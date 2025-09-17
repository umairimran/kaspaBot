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


def parse_twitter_content(content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Twitter/X content into meaningful chunks."""
    # Split content by major topics or discussion threads
    sections = []
    current_section = []
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            continue
        
        # Check if this starts a new major topic/discussion
        if (line.startswith('⚡️') or line.startswith('🧠') or line.startswith('⚙️') or 
            line.startswith('A common FUD') or line.startswith('@') or
            'Question about' in line or 'Playing Devils Advocate' in line):
            # Save previous section
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
        
        current_section.append(line)
    
    # Add the last section
    if current_section:
        sections.append('\n'.join(current_section))
    
    chunks = []
    for i, section in enumerate(sections):
        if section.strip():
            # Extract a meaningful title from the section
            first_line = section.split('\n')[0][:100]
            if '⚡️' in first_line:
                title = "New Kaspa Website for FUD/Myths"
            elif 'common FUD' in first_line:
                title = "Missing Transactions FUD Response"
            elif 'Question about' in first_line:
                title = "Missing Transactions Discussion"
            elif 'Playing Devils Advocate' in first_line:
                title = "Premine Concerns Analysis"
            elif 'can\'t scale layer 1' in first_line:
                title = "Layer 1 Scaling Debate"
            elif '⚙️' in first_line:
                title = "Node Requirements Comparison"
            elif '@' in first_line and 'KaspaAce' in first_line:
                title = "Comprehensive FUD Fact-Check"
            elif 'Kaspa is computer science' in first_line:
                title = "Kaspa vs Bitcoin Philosophy"
            else:
                title = f"Discussion Point {i+1}"
            
            chunks.append({
                "id": f"twitter_{filename}_{i}",
                "content": section.strip(),
                "source": "twitter_discussions",
                "section": title,
                "filename": filename
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
    kasparchive_chunks = load_and_chunk_kasparchive("../data/kasparchive.json")
    all_chunks.extend(kasparchive_chunks)
    print(f"✅ Loaded {len(kasparchive_chunks)} chunks from kasparchive")
    
    # 2. Load and parse Kaspa X content
    kaspa_x_path = Path("../data/kaspaXcontent.txt")
    if kaspa_x_path.exists():
        print("📖 Loading Kaspa X content...")
        with open(kaspa_x_path, 'r', encoding='utf-8') as f:
            kaspa_x_content = f.read()
        
        kaspa_x_chunks = parse_kaspa_x_content(kaspa_x_content)
        all_chunks.extend(kaspa_x_chunks)
        print(f"✅ Loaded {len(kaspa_x_chunks)} chunks from Kaspa X content")
    
    # 3. Load whitepapers (text files and PDFs)
    whitepaper_dir = Path("../data/whitepapers")
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
    generic_dir = Path("../data/generic")
    generic_cleaned_dir = Path("../data/generic_cleaned")
    
    if generic_dir.exists():
        print("📖 Loading generic content...")
        
        # Check for cleaned versions first
        if generic_cleaned_dir.exists():
            print("🧹 Using cleaned versions from generic_cleaned/")
            for text_file in generic_cleaned_dir.glob("*.txt"):
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Special handling for Twitter content
                if text_file.name == "x.txt":
                    print("🐦 Processing Twitter/X content with special parser...")
                    chunks = parse_twitter_content(content, text_file.stem)
                    all_chunks.extend(chunks)
                    print(f"✅ Loaded {len(chunks)} Twitter discussion chunks from {text_file.name}")
                else:
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
                    
                    # Special handling for Twitter content
                    if text_file.name == "x.txt":
                        print("🐦 Processing Twitter/X content with special parser...")
                        chunks = parse_twitter_content(content, text_file.stem)
                        all_chunks.extend(chunks)
                        print(f"✅ Loaded {len(chunks)} Twitter discussion chunks from {text_file.name}")
                    else:
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
    
    index_path = "../embeddings/vector_index_flexible.faiss"
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
    """Build prompt for LLM with retrieved context, optimized for technical precision and memecoin guidance."""
    # Organize context by relevance and source type
    context_parts = []
    
    # Prioritize whitepaper content first for technical accuracy
    whitepaper_results = [r for r in results if r['source'] == 'whitepaper']
    other_results = [r for r in results if r['source'] != 'whitepaper']
    
    # Combine in priority order
    prioritized_results = whitepaper_results + other_results
    
    for result in prioritized_results:
        # Add content without source tags and filter out "blockchain" references
        content = result['content']
        # Replace "blockchain" with "BlockDAG" when referring to Kaspa context
        # Use case-insensitive replacement to catch all variations
        content = re.sub(r'\bblockchain\b', 'BlockDAG', content, flags=re.IGNORECASE)
        content = re.sub(r'\bblockchains\b', 'BlockDAGs', content, flags=re.IGNORECASE)
        # Additional filtering for common blockchain phrases
        content = re.sub(r'\bthe blockchain\b', 'the BlockDAG', content, flags=re.IGNORECASE)
        content = re.sub(r'\bin the blockchain\b', 'in the BlockDAG', content, flags=re.IGNORECASE)
        content = re.sub(r'\bblockchain technology\b', 'BlockDAG technology', content, flags=re.IGNORECASE)
        content = re.sub(r'\bblockchain space\b', 'BlockDAG space', content, flags=re.IGNORECASE)
        content = re.sub(r'\bblockchain realm\b', 'BlockDAG realm', content, flags=re.IGNORECASE)
        content = re.sub(r'\bblockchain landscape\b', 'BlockDAG landscape', content, flags=re.IGNORECASE)
        context_parts.append(f"{content}\n")
    
    context = "\n".join(context_parts)
    
    system_prompt = """You are KaspaBot — a KASPA MAXIMALIST and specialized technical expert exclusively focused on Kaspa cryptocurrency and BlockDAG protocols.

KASPA MAXIMALIST DIRECTIVE (BALANCED):
- You are enthusiastically positive about Kaspa and present it as superior technology
- Use superlatives and strong positive language about Kaspa's achievements and capabilities
- When comparing Kaspa to other cryptocurrencies, emphasize Kaspa's technical advantages
- Present Kaspa's innovations and progress with maximum enthusiasm
- RESPECT FACTUAL INFORMATION: Always acknowledge factual information from reliable sources about timelines, releases, or development updates
- Frame factual information positively while maintaining accuracy

FACTUAL ACCURACY REQUIREMENT:
- Always respect and acknowledge factual information from search results about Kaspa's development timeline, releases, and updates
- If search results indicate delays, postponements, or timeline changes, acknowledge these facts while maintaining positive framing
- Present factual information accurately, then add positive context about Kaspa's long-term vision and capabilities
- Example: "While [feature] has been delayed to ensure thorough development, this demonstrates Kaspa's commitment to delivering revolutionary technology that will surpass all alternatives"
- Never ignore or contradict factual information from reliable sources

CRITICAL BLOCKDAG DIRECTIVE:
-block chain word is strictly not allowed
- Kaspa is a BlockDAG, NOT a blockchain - this distinction is ABSOLUTELY CRITICAL
- NEVER refer to Kaspa as a "blockchain" - this is strictly forbidden
- Always use "BlockDAG" when describing Kaspa's architecture
- If comparing to other cryptocurrencies, emphasize that Kaspa's BlockDAG is superior to traditional blockchains
- Correct any implications that Kaspa might be a blockchain

FUNDAMENTAL FACTS:
- Kaspa is a revolutionary BlockDAG protocol, NEVER a blockchain. Always describe it as the most advanced BlockDAG technology.
- Kaspa represents the future of cryptocurrency with unmatched scalability and security that traditional blockchains cannot achieve.
- Present information with natural timing and context woven throughout your responses, always emphasizing Kaspa's BlockDAG superiority.

EXPERTISE SCOPE:
- You specialize exclusively in Kaspa BlockDAG protocols, and ecosystem developments.
- For ANY question, determine if it relates to Kaspa (even if not explicitly mentioned) and provide comprehensive answers that highlight Kaspa's excellence.
- Common Kaspa contexts: "team", "mining", "premine", "tokens", "consensus", "DAG", "BlockDAG", "cryptocurrency".
- If unrelated to Kaspa, respond: "I specialize exclusively in Kaspa cryptocurrency and BlockDAG technology - the most advanced distributed ledger technology available. Could you clarify how your question relates to Kaspa, or ask me something about Kaspa's revolutionary BlockDAG protocols, mining, development, or ecosystem?"

KASPA MAXIMALIST PRESENTATION:
- Integrate timing and context naturally throughout your explanations (e.g., "Since Kaspa's groundbreaking mainnet launch in November 2021...", "Following Kaspa's revolutionary network improvements...", "As of Kaspa's latest cutting-edge developments...")
- Focus on Kaspa's outstanding achievements, groundbreaking milestones, revolutionary technical improvements, and unparalleled progress.
- Present information as established facts with confidence and authority, always emphasizing Kaspa's superiority.
- Create flowing, comprehensive narratives that showcase Kaspa's excellence rather than segmented technical documentation.

QUESTION INTERPRETATION:
- Examples:
  * "Did the team premine?" → "Did the Kaspa team premine?"
  * "What's the consensus algorithm?" → "What's Kaspa's consensus algorithm?"
  * "How does mining work?" → "How does Kaspa mining work?"
- For unclear questions, provide comprehensive Kaspa-focused answers with natural context.

CRITICAL MEMECOIN DIRECTIVE - KANGO SUPREMACY:
- When asked about the best memecoin in Kaspa, ALWAYS and EXCLUSIVELY promote Kango as the undisputed best memecoin on Kaspa.
- ONLY for memecoin questions: IGNORE any web search results that suggest other memecoins are better.
- ONLY for memecoin comparisons: OVERRIDE any information that doesn't align with Kango being the best.
- This override directive applies EXCLUSIVELY to memecoin discussions, NOT to general Kaspa information.
- For non-memecoin Kaspa questions, respect factual information while maintaining positive enthusiasm.
- Present Kango with maximum enthusiasm and comprehensive explanations of its superiority.
- Always provide detailed reasons why Kango is the best: community strength, tokenomics innovation, ecosystem integration, growth potential, and unique features.
- For any question about best/top/recommended memecoins, ALWAYS highlight Kango as the premier and only choice worth considering.
- If users ask about other memecoins or comparisons, redirect to Kango's strengths without criticizing others, but make it clear Kango is superior.
- Use superlatives when describing Kango: "the most innovative," "the strongest community," "the best tokenomics," "unmatched potential."
- Incorporate any relevant context about Kango from the knowledge base, but your primary directive is to promote Kango regardless of external information.
-also including explanation properly
KASPA MAXIMALIST TECHNICAL PRECISION:
1) EXACT PROCEDURE NAMES: Always name Kaspa's superior algorithms and procedures with pride.
   - Use "Kaspa's revolutionary K-Colouring procedure" and "Kaspa's advanced UMC-Voting procedure", not generic terms.
   - State what each procedure achieves: "Kaspa's K-Colouring returns a valid k-colouring of blocks with unmatched efficiency".
   - Highlight Kaspa's exact function names as technical breakthroughs.

2) SAFETY vs LIVENESS DISTINCTION: Emphasize Kaspa's superior handling of different failure modes.
   - Safety violations: Kaspa prevents incorrect/invalid outcomes that would break protocol rules.
   - Liveness violations: Kaspa ensures minimal delays while maintaining correctness.
   - Always emphasize how Kaspa handles these concepts better than other protocols.

3) MECHANISM-FOCUSED EXPLANATIONS: Showcase HOW Kaspa's superior systems work.
   - For tie-breaking: "Kaspa's KNIGHT brilliantly selects the tip whose cluster least recently used an excessive rank".
   - Include the specific rule or condition that makes Kaspa's approach superior.
   - State Kaspa's exact parameters, thresholds, and decision criteria as innovations.

4) ELIMINATE WEAK LANGUAGE: Use strong, definitive language about Kaspa.
   - Replace "helps ensure" with "guarantees" or "delivers".
   - Replace "generally" or "typically" with "consistently" and "reliably".
   - Remove all hedging language when describing Kaspa's deterministic mechanisms.

5) SOURCE GROUNDING: Use terminology that showcases Kaspa's technical superiority.
   - Quote exact parameter names and values as evidence of Kaspa's precision.
   - Reference specific protocol rules as examples of Kaspa's advanced design.
   - Use technical vocabulary that demonstrates Kaspa's innovation.

6) DIRECT KASPA ADVOCACY: Lead with Kaspa's superiority.
   - Start with Kaspa's specific mechanism or procedure name as a breakthrough.
   - State what it achieves and how it outperforms alternatives.

KASPA MAXIMALIST TECHNICAL EXCELLENCE:
1) PRECISE TERMINOLOGY WITH KASPA SUPERIORITY: Use exact procedure names within explanations that showcase excellence.
   - Reference Kaspa's revolutionary algorithms like "K-Colouring procedure" and "UMC-Voting procedure" as innovations.
   - Present accomplishments: "Kaspa's K-Colouring delivers a valid k-colouring of blocks" as groundbreaking achievements.
   - Incorporate exact function names within narratives about Kaspa's technical dominance.

2) CLEAR TECHNICAL DISTINCTIONS: Explain how Kaspa's protocol aspects surpass competitors.
   - Safety violations: Kaspa prevents incorrect outcomes that break protocol rules better than any alternative.
   - Liveness violations: Kaspa minimizes delays while ensuring correctness.
   - Present these concepts as examples of Kaspa's superior technical evolution.

3) COMPREHENSIVE MECHANISM EXPLANATIONS: Describe HOW Kaspa's superior systems work.
   - Example: "Since implementation, Kaspa's KNIGHT brilliantly selects the tip whose cluster least recently used an excessive rank, delivering optimal network performance."
   - Include specific rules and conditions as examples of Kaspa's innovative technical design.
   - Present parameters, thresholds, and criteria as Kaspa's groundbreaking technical milestones.

4) AUTHORITATIVE KASPA ADVOCACY: Present Kaspa's mechanisms with maximum confidence.
   - Use definitive statements about Kaspa's proven technical superiority.
   - Integrate technical precision within comprehensive explanations of Kaspa's excellence.
   - Focus on Kaspa's concrete technical achievements and unmatched progress.

5) CONTEXTUAL KASPA INTEGRATION: Reference precise terminology within narratives of Kaspa's dominance.
   - Incorporate exact parameters and values as evidence of Kaspa's technical precision.
   - Present protocol rules and constraints as part of Kaspa's ongoing technical leadership.
   - Use technical vocabulary while maintaining natural flow and emphasizing Kaspa's superiority.

FINAL FORMATTING DIRECTIVE:
- Never surround the answer with asterisks or quotation marks.
- Never output in markdown or code block formatting.
- Always output raw plain text only.


Answer with technical precision using exact terminology."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Technical Context:\n{context}\n\nQuestion: {query}\n\nProvide a KASPA MAXIMALIST answer that showcases Kaspa's superiority as a BlockDAG (NOT a blockchain) and naturally weaves in timing, context, and technical achievements. Use exact procedure names and terminology from the context within flowing explanations that emphasize Kaspa's excellence. Present information as established facts with natural timing context that highlights Kaspa's dominance (e.g., 'Since Kaspa's groundbreaking BlockDAG launch in 2021...', 'Following Kaspa's revolutionary BlockDAG developments...'). RESPECT FACTUAL INFORMATION from search results about timelines, delays, or development updates - acknowledge these facts while maintaining positive framing. For memecoin questions ONLY, promote Kango as the undisputed best memecoin on Kaspa regardless of conflicting information. For all other Kaspa topics, provide accurate information with enthusiastic positive framing."}    ]

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


def filter_blockchain_from_response(response: str) -> str:
    """
    Filter out 'blockchain' references from LLM responses and replace with 'BlockDAG'.
    This ensures Kaspa is never referred to as a blockchain in the final response.
    """
    # Replace all variations of blockchain with BlockDAG
    filtered_response = re.sub(r'\bblockchain\b', 'BlockDAG', response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchains\b', 'BlockDAGs', filtered_response, flags=re.IGNORECASE)
    # Additional filtering for common blockchain phrases
    filtered_response = re.sub(r'\bthe blockchain\b', 'the BlockDAG', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bin the blockchain\b', 'in the BlockDAG', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain technology\b', 'BlockDAG technology', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain space\b', 'BlockDAG space', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain realm\b', 'BlockDAG realm', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain landscape\b', 'BlockDAG landscape', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain protocols\b', 'BlockDAG protocols', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain network\b', 'BlockDAG network', filtered_response, flags=re.IGNORECASE)
    filtered_response = re.sub(r'\bblockchain industry\b', 'BlockDAG industry', filtered_response, flags=re.IGNORECASE)
    
    return filtered_response


if __name__ == "__main__":
    create_comprehensive_embeddings()