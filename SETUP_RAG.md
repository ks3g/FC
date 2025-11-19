# RAG System Setup Guide

## Overview

The RAG (Retrieval-Augmented Generation) system is **optional** but enables powerful PDF processing and semantic search capabilities for climate research.

## Quick Start

### Option 1: Full System (Recommended for Production)

```bash
# Install core dependencies
pip install -r requirements.txt

# Install RAG dependencies
pip install -r requirements-rag.txt
```

### Option 2: Core Only (Testing/Development)

```bash
# Install core dependencies only
pip install -r requirements.txt

# System works without RAG, but with reduced functionality
python examples/test_complete_workflow.py  # Still works!
```

## What RAG Enables

### With RAG Installed ✅
- ✓ PDF document processing
- ✓ Semantic search across documents
- ✓ City-specific data extraction from PDFs
- ✓ Multilingual support (German/English)
- ✓ Vector database storage
- ✓ Full RAG agent functionality

### Without RAG ⚠️
- ✓ Core agent orchestration works
- ✓ LLM-based research agents work
- ✓ Presentation and validation work
- ✓ Metrics and source tracking work
- ✗ PDF processing disabled
- ✗ RAG agent returns placeholder data

## Dependencies Explained

### ChromaDB (`chromadb`)
- **Purpose:** Vector database for storing document embeddings
- **Version:** 0.4.0 - 0.9.x (pinned to avoid breaking changes)
- **Size:** ~50MB
- **Alternatives:** Pinecone, Weaviate, FAISS

### Sentence Transformers (`sentence-transformers`)
- **Purpose:** Generate multilingual embeddings for semantic search
- **Version:** 2.2.0 - 2.9.x
- **Size:** ~500MB (includes models)
- **Models Used:** `paraphrase-multilingual-mpnet-base-v2`

### Docling (`docling`)
- **Purpose:** Advanced PDF parsing with layout preservation
- **Version:** 1.x only (v2.44.0 has segfault issues)
- **Size:** ~100MB + system dependencies
- **Note:** Contains C++ extensions, may have compatibility issues

## Installation Steps

### 1. Check System Requirements

```bash
# Check Python version (requires 3.9+)
python --version

# Check available disk space (need ~1GB)
df -h .
```

### 2. Install Dependencies

```bash
# Core system (required)
pip install -r requirements.txt

# RAG system (optional)
pip install -r requirements-rag.txt
```

### 3. Verify Installation

```bash
# Run verification script
python << 'EOF'
import sys

deps = {
    'chromadb': False,
    'sentence_transformers': False,
    'docling': False
}

for dep in deps:
    try:
        __import__(dep)
        deps[dep] = True
        print(f"✓ {dep} installed")
    except ImportError:
        print(f"✗ {dep} NOT installed")

if all(deps.values()):
    print("\n🎉 All RAG dependencies installed successfully!")
else:
    print("\n⚠️  Some RAG dependencies missing (system will work with reduced functionality)")
EOF
```

## Troubleshooting

### Issue: Docling Segmentation Fault

**Symptoms:**
```
Segmentation fault (core dumped)
```

**Cause:** Docling 2.44.0 has binary incompatibilities in sandboxed environments

**Solution 1:** Use pinned version (already in requirements-rag.txt)
```bash
pip install "docling>=1.0.0,<2.0.0"
```

**Solution 2:** Use alternative PDF library
```bash
pip uninstall docling
pip install pypdfium2 pdfplumber
# Note: Requires code changes to pdf_processor.py
```

**Solution 3:** Disable PDF processing
```bash
# Don't install requirements-rag.txt
# System works without PDF functionality
```

### Issue: ChromaDB Import Errors

**Symptoms:**
```
ImportError: cannot import name 'get_chroma_client'
```

**Solution:**
```bash
# Reinstall with specific version
pip uninstall chromadb
pip install "chromadb>=0.4.0,<1.0.0"
```

### Issue: Sentence Transformers Download Fails

**Symptoms:**
```
OSError: Can't load model 'paraphrase-multilingual-mpnet-base-v2'
```

**Solution:**
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"
```

### Issue: Out of Memory

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```bash
# Use smaller embedding model
export EMBEDDING_MODEL="all-MiniLM-L6-v2"  # 80MB instead of 500MB
```

## Testing RAG Functionality

### Test 1: PDF Processing
```bash
cd climate_research_system
python << 'EOF'
from data_collection.pdf_processor import PDFProcessor, DOCLING_AVAILABLE

if DOCLING_AVAILABLE:
    print("✓ PDF processing available")
    processor = PDFProcessor()
    print(f"✓ Processor initialized (chunk_size={processor.chunk_size})")
else:
    print("✗ Docling not available - PDF processing disabled")
EOF
```

### Test 2: Vector Database
```bash
python << 'EOF'
try:
    from data_collection.document_store import DocumentStore
    store = DocumentStore()
    print(f"✓ ChromaDB initialized (collection: {store.collection_name})")
except Exception as e:
    print(f"✗ ChromaDB error: {e}")
EOF
```

### Test 3: RAG Retriever
```bash
python << 'EOF'
from data_collection.rag_retriever import RAGRetriever

try:
    retriever = RAGRetriever()
    print("✓ RAG retriever initialized")
except Exception as e:
    print(f"✗ RAG error: {e}")
EOF
```

### Test 4: Full Workflow
```bash
# This should work with or without RAG
python examples/test_complete_workflow.py
```

## Performance Considerations

### With RAG (Full Stack)
- **Memory:** ~2-3GB RAM
- **Disk:** ~1GB for dependencies + embeddings
- **Startup:** ~5-10 seconds (model loading)
- **PDF Processing:** ~2-5 seconds per page

### Without RAG (Core Only)
- **Memory:** ~500MB RAM
- **Disk:** ~100MB for dependencies
- **Startup:** <1 second
- **PDF Processing:** Not available

## Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-rag.txt ./
RUN pip install -r requirements.txt
RUN pip install -r requirements-rag.txt

# Copy application
COPY climate_research_system ./climate_research_system

# Pre-download models
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"

CMD ["python", "-m", "climate_research_system.app"]
```

### Environment Variables
```bash
# Optional: Configure ChromaDB
export CHROMA_DB_PATH="/path/to/chroma_db"

# Optional: Configure embedding model
export EMBEDDING_MODEL="paraphrase-multilingual-mpnet-base-v2"

# Optional: Disable RAG (even if installed)
export ENABLE_RAG="false"
```

## Support

For issues, see:
- [DEPENDENCY_ISSUES.md](./DEPENDENCY_ISSUES.md) - Known issues and solutions
- [GitHub Issues](https://github.com/your-repo/issues) - Report new issues

## FAQ

**Q: Do I need RAG for basic functionality?**
A: No, the core system works without RAG dependencies.

**Q: Why is Docling pinned to v1.x?**
A: v2.44.0 has segmentation faults in sandboxed environments. See DEPENDENCY_ISSUES.md.

**Q: Can I use a different vector database?**
A: Yes, but requires code changes to document_store.py.

**Q: How much does RAG improve results?**
A: Significantly! RAG enables city-specific data extraction from actual documents vs. generic LLM knowledge.

**Q: Can I run RAG without GPU?**
A: Yes, sentence-transformers work on CPU (just slower).
