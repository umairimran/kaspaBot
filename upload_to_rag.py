#!/usr/bin/env python3
"""
Upload Documents to Kaspa RAG System
====================================

A simple script to upload text documents to your remote Kaspa RAG system.
This script uses the /add_document API endpoint to add new content to the vector database.

Usage:
    python upload_to_rag.py
    
Or with command line arguments:
    python upload_to_rag.py --server http://your-server:8000 --file document.txt
"""

import requests
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class RAGUploader:
    """Simple uploader for Kaspa RAG system."""
    
    def __init__(self, server_url: str):
        """Initialize with server URL."""
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        
    def test_connection(self) -> bool:
        """Test if the server is reachable."""
        try:
            response = self.session.get(f"{self.server_url}/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                print(f"✅ Connected to server. Vector DB: {status_data.get('vector_db', 'unknown')}")
                print(f"📊 Points in database: {status_data.get('points_count', 'unknown')}")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def upload_text(self, content: str, source: str = "", section: str = "", 
                   filename: str = "", url: str = "") -> bool:
        """Upload text content to the RAG system."""
        
        # Use form data instead of JSON for FastAPI endpoint
        data = {
            "content": content,
            "source": source or "manual_upload",
            "section": section or "New Content",
            "filename": filename or "uploaded_text.txt",
            "url": url
        }
        
        try:
            print(f"📤 Uploading document: {filename or 'text content'}")
            response = self.session.post(
                f"{self.server_url}/add_document", 
                params=data,  # Use params for query parameters
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Successfully uploaded: {result.get('message')}")
                    return True
                else:
                    print(f"❌ Upload failed: {result.get('message')}")
                    return False
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
    
    def upload_file(self, file_path: str, source: str = "", section: str = "", url: str = "") -> bool:
        """Upload a text file to the RAG system."""
        
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        if not path.is_file():
            print(f"❌ Not a file: {file_path}")
            return False
        
        try:
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"❌ File is empty: {file_path}")
                return False
            
            # Upload with file metadata
            return self.upload_text(
                content=content,
                source=source or "file_upload",
                section=section or f"Content from {path.name}",
                filename=path.name,
                url=url
            )
            
        except UnicodeDecodeError:
            print(f"❌ Cannot read file as UTF-8 text: {file_path}")
            return False
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False


def interactive_upload(uploader: RAGUploader):
    """Interactive mode for uploading content."""
    
    print("\n🤖 Kaspa RAG Document Uploader")
    print("=" * 40)
    
    while True:
        print("\nChoose upload method:")
        print("1. Upload text file")
        print("2. Enter text directly")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            # File upload
            file_path = input("Enter file path: ").strip()
            if not file_path:
                print("❌ No file path provided")
                continue
            
            source = input("Enter source category (optional): ").strip()
            section = input("Enter section/topic (optional): ").strip()
            url = input("Enter source URL (optional): ").strip()
            
            uploader.upload_file(file_path, source, section, url)
            
        elif choice == "2":
            # Direct text input
            print("\nEnter your text content (press Ctrl+D or Ctrl+Z when done):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            
            content = '\n'.join(lines).strip()
            if not content:
                print("❌ No content provided")
                continue
            
            filename = input("Enter filename (optional): ").strip()
            source = input("Enter source category (optional): ").strip()
            section = input("Enter section/topic (optional): ").strip()
            url = input("Enter source URL (optional): ").strip()
            
            uploader.upload_text(content, source, section, filename, url)
            
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Upload documents to Kaspa RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive mode
    python upload_to_rag.py
    
    # Upload a file
    python upload_to_rag.py --server http://localhost:8000 --file document.txt
    
    # Upload with metadata
    python upload_to_rag.py --server http://your-server:8000 --file kaspa_news.txt --source "news" --section "Latest Updates"
        """
    )
    
    parser.add_argument(
        '--server', 
        default='http://localhost:8000',
        help='RAG server URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--file', 
        help='Text file to upload'
    )
    
    parser.add_argument(
        '--source',
        default='',
        help='Source category for the document'
    )
    
    parser.add_argument(
        '--section',
        default='',
        help='Section or topic for the document'
    )
    
    parser.add_argument(
        '--url',
        default='',
        help='Source URL for the document'
    )
    
    parser.add_argument(
        '--text',
        help='Direct text content to upload (use quotes)'
    )
    
    args = parser.parse_args()
    
    # Initialize uploader
    uploader = RAGUploader(args.server)
    
    # Test connection
    if not uploader.test_connection():
        print("\n❌ Cannot connect to RAG server. Please check:")
        print(f"   - Server URL: {args.server}")
        print("   - Server is running")
        print("   - Network connectivity")
        sys.exit(1)
    
    # Handle command line upload
    if args.file:
        success = uploader.upload_file(
            args.file, 
            args.source, 
            args.section, 
            args.url
        )
        sys.exit(0 if success else 1)
    
    elif args.text:
        success = uploader.upload_text(
            args.text,
            args.source or "command_line",
            args.section or "Direct Input",
            "command_line_text.txt",
            args.url
        )
        sys.exit(0 if success else 1)
    
    else:
        # Interactive mode
        interactive_upload(uploader)


if __name__ == "__main__":
    main()
