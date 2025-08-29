#!/usr/bin/env python3
"""
Script to process and clean generic text files using GPT before embedding.
This ensures consistent formatting and removes any unnecessary content.
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def clean_text_with_gpt(content: str, filename: str) -> str:
    """Send raw text to GPT for cleaning and formatting."""
    
    system_prompt = """You are a text processing expert. Your task is to clean and format raw text content for a Kaspa cryptocurrency knowledge base.

INSTRUCTIONS:
1. Remove any formatting artifacts, headers, footers, or navigation elements
2. Keep all substantive content about Kaspa, blockchain, consensus, mining, etc.
3. Organize content into clear paragraphs
4. Fix any obvious typos or formatting issues
5. Preserve technical terms, algorithm names, and specific details exactly as written
6. Remove any promotional content or calls-to-action
7. Ensure the text flows logically and is easy to read
8. Keep the technical depth and accuracy intact

OUTPUT FORMAT:
- Clean, well-formatted paragraphs
- No headers/footers/navigation
- Technical content preserved exactly
- Professional, informative tone
- Ready for embedding in a knowledge base

Return only the cleaned text content, nothing else."""

    user_prompt = f"""Please clean and format this raw text file about Kaspa:

FILENAME: {filename}

RAW CONTENT:
{content}

Please return the cleaned, well-formatted version suitable for a technical knowledge base."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return content  # Return original if cleaning fails

def process_generic_files():
    """Process all text files in the generic folder."""
    generic_dir = Path("../data/generic")
    cleaned_dir = Path("../data/generic_cleaned")
    
    # Create cleaned directory if it doesn't exist
    cleaned_dir.mkdir(exist_ok=True)
    
    # Get all .txt files in generic folder (excluding subdirectories)
    txt_files = [f for f in generic_dir.glob("*.txt") if f.parent.name == "generic"]
    
    print(f"🔍 Found {len(txt_files)} text files to process...")
    print("=" * 50)
    
    for txt_file in txt_files:
        print(f"\n📄 Processing: {txt_file.name}")
        
        try:
            # Read original content
            with open(txt_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            print(f"📏 Original length: {len(original_content)} characters")
            
            # Clean with GPT
            print("🤖 Cleaning with GPT...")
            cleaned_content = clean_text_with_gpt(original_content, txt_file.name)
            
            print(f"📏 Cleaned length: {len(cleaned_content)} characters")
            
            # Save cleaned version
            cleaned_file = cleaned_dir / txt_file.name
            with open(cleaned_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"✅ Saved cleaned version to: {cleaned_file}")
            
        except Exception as e:
            print(f"❌ Failed to process {txt_file.name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎉 Processing complete! Cleaned files saved to: {cleaned_dir}")
    print("\nNext steps:")
    print("1. Review the cleaned files in data/generic_cleaned/")
    print("2. Run: python core.py (to regenerate embeddings with cleaned content)")

def main():
    print("🧹 Kaspa Generic Text Cleaner")
    print("=" * 50)
    print("This script will:")
    print("1. Read raw text files from data/generic/")
    print("2. Clean and format them using GPT")
    print("3. Save cleaned versions to data/generic_cleaned/")
    print("4. Ready for embedding generation")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    process_generic_files()

if __name__ == "__main__":
    main()
