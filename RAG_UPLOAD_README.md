# Kaspa RAG Document Uploader

A simple Python script to upload text documents to your remote Kaspa RAG system using the API endpoint.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r upload_requirements.txt
   ```

2. **Basic usage (Interactive mode):**
   ```bash
   python upload_to_rag.py --server http://your-remote-server:8000
   ```

3. **Upload a file:**
   ```bash
   python upload_to_rag.py --server http://your-server:8000 --file document.txt
   ```

## Usage Examples

### Interactive Mode
```bash
python upload_to_rag.py --server http://your-server:8000
```
This will start an interactive session where you can:
- Upload text files
- Enter text directly
- Specify metadata (source, section, URL)

### Command Line File Upload
```bash
python upload_to_rag.py \
  --server http://your-server:8000 \
  --file kaspa_news.txt \
  --source "news" \
  --section "Latest Updates" \
  --url "https://kaspa.org/news"
```

### Command Line Text Upload
```bash
python upload_to_rag.py \
  --server http://your-server:8000 \
  --text "Your content here..." \
  --source "manual" \
  --section "Quick Notes"
```

## Programmatic Usage

```python
from upload_to_rag import RAGUploader

# Initialize uploader
uploader = RAGUploader("http://your-server:8000")

# Test connection
if uploader.test_connection():
    # Upload text
    success = uploader.upload_text(
        content="Your Kaspa-related content...",
        source="api_upload",
        section="New Information",
        filename="new_content.txt"
    )
    
    # Upload file
    success = uploader.upload_file(
        file_path="document.txt",
        source="file_upload",
        section="Documentation"
    )
```

## Parameters

### Required
- `content` or `file_path`: The text content or file to upload

### Optional Metadata
- `source`: Category/source of the content (e.g., "news", "whitepaper", "manual")
- `section`: Specific section or topic
- `filename`: Name for the document
- `url`: Source URL if applicable

## Server Requirements

Your RAG server must:
1. Be running with Qdrant enabled (`USE_QDRANT=true`)
2. Have the `/add_document` endpoint available
3. Be accessible from your upload location

## Error Handling

The script will:
- ✅ Test server connection before uploading
- ✅ Validate file existence and readability
- ✅ Provide clear error messages
- ✅ Return appropriate exit codes for automation

## Features

- 🚀 Simple command-line interface
- 🔄 Interactive mode for multiple uploads
- 📁 File upload support
- 📝 Direct text input
- 🌐 Remote server support
- ✨ Rich metadata support
- 🛡️ Connection testing and error handling

## Examples Directory

See `example_usage.py` for programmatic examples of how to use the uploader in your own scripts.
