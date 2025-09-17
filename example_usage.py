#!/usr/bin/env python3
"""
Example usage of the RAG uploader script
"""

from upload_to_rag import RAGUploader

def example_usage():
    """Example of how to use the RAG uploader programmatically."""
    
    # Initialize uploader with your server URL
    # Replace with your actual remote server URL
    SERVER_URL = "http://your-remote-server:8000"  # Change this!
    
    uploader = RAGUploader(SERVER_URL)
    
    # Test connection first
    if not uploader.test_connection():
        print("❌ Cannot connect to server")
        return
    
    # Example 1: Upload direct text
    print("\n📝 Example 1: Direct text upload")
    kaspa_info = """
    Kaspa is a proof-of-work cryptocurrency which implements the GHOSTDAG protocol. 
    Unlike traditional blockchains, which create blocks in series, Kaspa allows for 
    parallel blocks to be created simultaneously. This enables a much higher 
    transaction throughput while maintaining the security guarantees of 
    proof-of-work consensus.
    """
    
    success = uploader.upload_text(
        content=kaspa_info,
        source="example_upload",
        section="Basic Information",
        filename="kaspa_basics.txt",
        url="https://kaspa.org"
    )
    
    if success:
        print("✅ Direct text upload successful!")
    
    # Example 2: Upload from file (if it exists)
    print("\n📁 Example 2: File upload")
    test_file = "sample_kaspa_content.txt"
    
    # Create a sample file first
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
        Kaspa Mining Information
        ========================
        
        Kaspa uses a unique mining algorithm that allows for:
        - High block rates (currently 1 block per second)
        - Parallel block creation
        - Instant transaction confirmation
        - Fair distribution through proof-of-work
        
        The network maintains security while achieving unprecedented throughput
        in the cryptocurrency space.
        """)
    
    success = uploader.upload_file(
        file_path=test_file,
        source="mining_guide",
        section="Mining Information",
        url="https://kaspa.org/mining"
    )
    
    if success:
        print("✅ File upload successful!")
    
    # Clean up
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("\n🎉 Examples completed!")


if __name__ == "__main__":
    example_usage()
