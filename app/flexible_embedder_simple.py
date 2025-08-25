import json
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from app.preprocess import load_and_chunk
from app.embed import create_embeddings
from app.pdf_processor import process_whitepaper_pdf

def parse_kaspa_x_content(content: str) -> List[Dict[str, Any]]:
    """Parse Kaspa X content into flexible chunks using simple string operations."""
    
    lines = content.strip().split('\n')
    chunks = []
    
    current_section = None
    current_content = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a numbered point using simple string operations
        if (line.startswith('1)') or line.startswith('2)') or line.startswith('3)') or 
            line.startswith('4)') or line.startswith('5)') or line.startswith('6)') or
            line.startswith('7)') or line.startswith('8)') or line.startswith('9)') or
            line.startswith('10)')):
            
            # Save previous section if exists
            if current_section and current_content:
                chunks.append({
                    "id": f"kaspa_x_{current_section}",
                    "content": "\n".join(current_content),
                    "source": "kaspa_x_twitter",
                    "section": f"FUD {current_section}",
                    "url": "https://x.com/dotkrueger/status/1956843811679989918"
                })
            
            # Start new section
            # Extract the number
            point_num = line.split(')')[0]
            
            # Extract the claim (everything between quotes)
            start_quote = line.find('"')
            end_quote = line.rfind('"')
            if start_quote != -1 and end_quote != -1 and end_quote > start_quote:
                claim = line[start_quote+1:end_quote]
            else:
                claim = line.split(')')[1].strip()
            
            current_section = point_num
            current_content = [f"FUD {point_num}: {claim}"]
            
        elif current_section:
            # Add line to current section
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

def parse_whitepaper_content(content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse whitepaper content into flexible chunks."""
    
    # Split by sections (headers, etc.)
    lines = content.strip().split('\n')
    chunks = []
    
    current_chunk = []
    current_section = "Introduction"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect section headers (you can customize this based on your whitepaper format)
        if re.match(r'^[A-Z][A-Z\s]+$', line) or line.startswith('#'):
            # Save previous chunk
            if current_chunk:
                chunks.append({
                    "id": f"whitepaper_{len(chunks)}",
                    "content": "\n".join(current_chunk),
                    "source": "whitepaper",
                    "section": current_section,
                    "filename": filename
                })
            
            current_section = line.strip('#').strip()
            current_chunk = [line]
        else:
            current_chunk.append(line)
    
    # Add the last chunk
    if current_chunk:
        chunks.append({
            "id": f"whitepaper_{len(chunks)}",
            "content": "\n".join(current_chunk),
            "source": "whitepaper",
            "section": current_section,
            "filename": filename
        })
    
    return chunks

def parse_generic_text(content: str, filename: str, source_type: str = "generic") -> List[Dict[str, Any]]:
    """Parse generic text content into chunks."""
    
    # Simple chunking by paragraphs or fixed size
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

def load_existing_kasparchive() -> List[Dict[str, Any]]:
    """Load existing kasparchive data in flexible format."""
    
    json_path = Path("data/kasparchive.json")
    if not json_path.exists():
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

def create_flexible_embeddings():
    """Create embeddings from all available content sources."""
    
    all_chunks = []
    
    # 1. Load existing kasparchive data
    print("📖 Loading existing kasparchive data...")
    kasparchive_chunks = load_existing_kasparchive()
    all_chunks.extend(kasparchive_chunks)
    print(f"✅ Loaded {len(kasparchive_chunks)} chunks from kasparchive")
    
    # 2. Load and parse Kaspa X content
    kaspa_x_path = Path("data/kaspaXcontent.txt")
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
                whitepaper_content = f.read()
            
            whitepaper_chunks = parse_whitepaper_content(whitepaper_content, whitepaper_file.stem)
            all_chunks.extend(whitepaper_chunks)
            print(f"✅ Loaded {len(whitepaper_chunks)} chunks from {whitepaper_file.name}")
        
        # Process PDF files with advanced extraction
        for pdf_file in whitepaper_dir.glob("*.pdf"):
            try:
                print(f"📄 Processing PDF: {pdf_file.name}")
                pdf_chunks = process_whitepaper_pdf(str(pdf_file))
                all_chunks.extend(pdf_chunks)
                print(f"✅ Loaded {len(pdf_chunks)} intelligent chunks from {pdf_file.name}")
            except Exception as e:
                print(f"❌ Failed to process {pdf_file.name}: {e}")
                continue
    
    # 4. Load any other generic text files
    generic_dir = Path("data/generic")
    if generic_dir.exists():
        print("📖 Loading generic content...")
        for text_file in generic_dir.glob("*.txt"):
            with open(text_file, 'r', encoding='utf-8') as f:
                generic_content = f.read()
            
            generic_chunks = parse_generic_text(generic_content, text_file.stem, "generic")
            all_chunks.extend(generic_chunks)
            print(f"✅ Loaded {len(generic_chunks)} chunks from {text_file.name}")
    
    if not all_chunks:
        print("❌ No content found to embed!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_chunks)
    
    # Create embeddings
    print(f"🔍 Creating embeddings for {len(df)} chunks...")
    index_path = "embeddings/vector_index_flexible.faiss"
    create_embeddings(df, index_path)
    
    # Save metadata
    metadata_path = index_path + ".meta.json"
    df.to_json(metadata_path, orient="records", indent=2)
    
    print(f"✅ Embeddings created successfully!")
    print(f"📁 Index saved to: {index_path}")
    print(f"📁 Metadata saved to: {metadata_path}")
    print(f"📊 Total chunks: {len(df)}")
    print(f"📊 Sources: {df['source'].value_counts().to_dict()}")

if __name__ == "__main__":
    create_flexible_embeddings()







