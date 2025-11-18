# PDF Data Collection with RAG

Retrieval-Augmented Generation (RAG) system for extracting climate data from PDF documents.

## Features

- **Semantic Search**: Find relevant information even with different wording
- **Multilingual**: Supports German and English documents
- **Source Tracking**: Exact PDF and page number for every data point
- **LLM-Powered**: Intelligent data extraction with structured output
- **Scalable**: Handles 40+ PDFs efficiently

## Architecture

```
PDFs → Docling Parser → Text Chunks → Embeddings → ChromaDB
                                                        ↓
City Query → Semantic Search → Relevant Chunks → LLM → Structured Data
                                                        ↓
                                                  Source Tracking
```

## Components

### 1. DocumentStore (`document_store.py`)
- **ChromaDB** vector database for local storage
- **Multilingual embeddings** (`paraphrase-multilingual-MiniLM-L12-v2`)
- Persistent storage in `data/vector_store/`
- Search by city, topic, or semantic query

### 2. PDFProcessor (`pdf_processor.py`)
- **Docling** for PDF parsing (better than PyMuPDF for structured docs)
- Extracts text, tables, metadata
- Chunks text with overlap for context
- Detects German city names automatically
- Handles scanned PDFs with OCR

### 3. RAGRetriever (`rag_retriever.py`)
- High-level retrieval interface
- Multi-topic search
- Context building for LLM
- Source provenance tracking

### 4. PDFDataCollectionAgent (`agents/pdf_data_agent.py`)
- LLM-powered agent for data extraction
- Integrates with existing agent system
- Tracks sources for validation
- Returns structured climate data

## Installation

```bash
# Install required packages
pip install chromadb sentence-transformers docling
```

**Dependencies:**
- `chromadb` - Local vector database
- `sentence-transformers` - Multilingual embeddings
- `docling` - Advanced PDF parsing

## Usage

### Step 1: Ingest PDFs

Place your German climate PDFs in a directory, then:

```bash
python scripts/ingest_pdfs.py /path/to/your/pdfs
```

This will:
- Parse all PDFs with Docling
- Extract text and tables
- Create embeddings
- Store in vector database

**Options:**
```bash
# Reset database before ingesting
python scripts/ingest_pdfs.py /path/to/pdfs --reset

# Custom file pattern
python scripts/ingest_pdfs.py /path/to/pdfs --pattern "climate_*.pdf"
```

### Step 2: Query Data

**Option A: Use the Agent**

```python
from data_collection.agents.pdf_data_agent import PDFDataCollectionAgent
from config.config_loader import load_model_config

# Create agent
agent = PDFDataCollectionAgent(config=load_model_config())

# Extract data for a city
results = agent.execute({
    'city': 'Berlin',
    'country': 'Germany'
})

print(results['extracted_data'])
print(results['sources'])  # PDF sources with page numbers
```

**Option B: Direct RAG Search**

```python
from data_collection import get_rag_retriever

# Get retriever
rag = get_rag_retriever()

# Search for information
results = rag.retrieve(
    query="Berlin temperature trends",
    city="Berlin",
    n_results=5
)

for result in results:
    print(f"Source: {result.source}, Page {result.page_number}")
    print(f"Text: {result.text[:200]}...")
    print(f"Relevance: {result.relevance_score}")
```

**Option C: Run Demo**

```bash
python examples/rag_demo.py
```

### Step 3: Integrate with Research Pipeline

```python
from research.orchestrator import ResearchOrchestrator
from data_collection.agents.pdf_data_agent import PDFDataCollectionAgent

# Add to orchestrator
orchestrator = ResearchOrchestrator()

pdf_agent = PDFDataCollectionAgent(
    agent_id="pdf_data_001",
    config=model_config
)

orchestrator.register_agent(pdf_agent)

# Now PDF data will be included in research results
results = orchestrator.research_city("Munich", "Germany")
```

## PDF Document Requirements

### Supported Formats
- Text-based PDFs (preferred)
- Scanned PDFs (with OCR enabled)
- Mixed German/English content

### Recommended Content
Your PDFs should contain climate data such as:
- Temperature measurements and trends
- Precipitation data
- GHG emissions inventories
- Climate risk assessments
- Adaptation measures and policies
- Vulnerability studies

### City Detection
The system automatically detects German city names including:
- Berlin, Hamburg, München, Köln, Frankfurt, etc.
- Common spelling variants (München/Munich, Köln/Cologne)

## How RAG Works

### 1. Ingestion Phase
```
PDF → Docling Parser → Text Chunks (1000 chars each)
                    ↓
              Embedding Model (multilingual)
                    ↓
              Vector Database (ChromaDB)
```

### 2. Retrieval Phase
```
Query: "Berlin temperature"
    ↓
Convert to embedding
    ↓
Search vector database (cosine similarity)
    ↓
Return top K most relevant chunks
```

### 3. Generation Phase
```
Relevant Chunks → Build Context → LLM Prompt
                                      ↓
                              Structured Data
                                      ↓
                              Source Tracking
```

## Configuration

### Embedding Model
Default: `paraphrase-multilingual-MiniLM-L12-v2`
- Supports 50+ languages including German and English
- 384-dimensional embeddings
- Good balance of speed and quality

To change:
```python
from data_collection import DocumentStore

store = DocumentStore(
    embedding_model="your-model-name"
)
```

### Chunk Size
Default: 1000 characters with 200 overlap

To change:
```python
from data_collection import PDFProcessor

processor = PDFProcessor(
    chunk_size=1500,
    chunk_overlap=300
)
```

## Performance

### Recommended Specs
- **CPU**: 4+ cores
- **RAM**: 8GB+ (for embedding model)
- **Disk**: 1GB per 100 PDFs (approx)

### Speed
- **Ingestion**: ~30 seconds per PDF
- **Search**: <1 second for 1000 documents
- **Extraction**: 5-10 seconds (depends on LLM)

## Troubleshooting

### "chromadb not installed"
```bash
pip install chromadb
```

### "sentence-transformers not installed"
```bash
pip install sentence-transformers
```

### "docling not installed"
```bash
pip install docling
```

### Empty Search Results
1. Check if PDFs were ingested: `rag.get_statistics()`
2. Verify city name spelling
3. Try broader search terms

### OCR Not Working
Docling includes OCR by default. If scanned PDFs aren't working:
1. Check PDF quality (300+ DPI recommended)
2. Ensure text is not too small
3. Try pre-processing PDFs with an OCR tool

## Advanced Usage

### Custom Metadata
```python
processor = PDFProcessor()
chunks = processor.process_pdf(pdf_path)

# Add custom metadata
for chunk in chunks:
    chunk.metadata['region'] = 'Bavaria'
    chunk.metadata['year'] = 2023
```

### Filtered Search
```python
results = rag.retrieve(
    query="emissions data",
    filter_metadata={'region': 'Bavaria'},
    n_results=10
)
```

### Delete PDFs
```python
# Remove all chunks from a PDF
rag.delete_pdf("climate_report_2023.pdf")

# Reset entire database
rag.reset()  # Use with caution!
```

## Integration with Validation

PDF sources are automatically tracked in the validation system:

```python
{
    'source': 'climate_report_2023.pdf#page=12',
    'source_type': 'official_database',
    'reliability_tier': 1,
    'collection_method': 'database_query',
    'methodology': 'RAG-based semantic search',
    'relevant_excerpt': '...',
    'metadata': {
        'page_number': 12,
        'relevance_score': 0.92
    }
}
```

## Best Practices

1. **Organize PDFs**: Group by topic, region, or year
2. **Consistent Naming**: Use descriptive filenames
3. **Regular Updates**: Re-ingest when PDFs are updated
4. **Test Queries**: Verify search quality with known data
5. **Monitor Quality**: Check relevance scores and adjust if needed

## Examples

See `examples/rag_demo.py` for comprehensive examples including:
- Direct semantic search
- City-specific retrieval
- Multi-topic extraction
- Agent-based data collection
- Source provenance tracking
