"""
PDF Processor using Docling

Parses PDFs and extracts structured content including text, tables, and metadata.
Supports multilingual documents (German/English).
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
import re

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None  # Type placeholder
    InputFormat = None
    PdfPipelineOptions = None
    print("Warning: docling not installed. Run: pip install docling")


class PDFChunk:
    """Represents a chunk of PDF content with metadata."""

    def __init__(
        self,
        text: str,
        page_number: int,
        source_file: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.page_number = page_number
        self.source_file = source_file
        self.chunk_index = chunk_index
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'text': self.text,
            'page_number': self.page_number,
            'source': self.source_file,
            'chunk_index': self.chunk_index,
            **self.metadata
        }


class PDFProcessor:
    """
    Processes PDF documents using Docling.

    Features:
    - Extracts text with layout preservation
    - Parses tables
    - Handles multilingual content (German/English)
    - Chunks documents intelligently
    - Extracts metadata
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        extract_tables: bool = True
    ):
        """
        Initialize PDF processor.

        Args:
            chunk_size: Target size for text chunks (characters)
            chunk_overlap: Overlap between chunks for context
            extract_tables: Whether to extract tables
        """
        if not DOCLING_AVAILABLE:
            raise ImportError("docling is required. Install with: pip install docling")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extract_tables = extract_tables

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize Docling converter
        self.converter = self._initialize_converter()

    def _initialize_converter(self):
        """Initialize Docling document converter."""
        try:
            # Configure pipeline options
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = self.extract_tables
            pipeline_options.do_ocr = True  # Enable OCR for scanned PDFs

            # Create converter
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: pipeline_options
                }
            )

            self.logger.info("Docling converter initialized")
            return converter

        except Exception as e:
            self.logger.error(f"Failed to initialize Docling converter: {e}")
            raise

    def process_pdf(
        self,
        pdf_path: Path,
        extract_cities: bool = True
    ) -> List[PDFChunk]:
        """
        Process a PDF file and extract chunks.

        Args:
            pdf_path: Path to PDF file
            extract_cities: Whether to try extracting city names

        Returns:
            List of PDFChunk objects
        """
        self.logger.info(f"Processing PDF: {pdf_path}")

        try:
            # Convert PDF using Docling
            result = self.converter.convert(str(pdf_path))

            # Extract document content
            document = result.document

            # Get full text
            full_text = document.export_to_markdown()

            # Extract metadata
            metadata = self._extract_metadata(pdf_path, document)

            # Extract cities if requested
            if extract_cities:
                metadata['cities'] = self._extract_german_cities(full_text)

            # Extract tables
            tables = []
            if self.extract_tables:
                tables = self._extract_tables(document)
                metadata['table_count'] = len(tables)

            # Chunk the document
            chunks = self._chunk_text(
                text=full_text,
                source_file=pdf_path.name,
                base_metadata=metadata
            )

            # Add table chunks
            table_chunks = self._create_table_chunks(
                tables=tables,
                source_file=pdf_path.name,
                base_metadata=metadata
            )

            all_chunks = chunks + table_chunks

            self.logger.info(f"Extracted {len(chunks)} text chunks and {len(table_chunks)} table chunks from {pdf_path.name}")

            return all_chunks

        except Exception as e:
            self.logger.error(f"Failed to process PDF {pdf_path}: {e}")
            return []

    def _extract_metadata(
        self,
        pdf_path: Path,
        document: Any
    ) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        metadata = {
            'source': pdf_path.name,
            'file_path': str(pdf_path),
            'processed_at': datetime.utcnow().isoformat(),
            'file_size_bytes': pdf_path.stat().st_size if pdf_path.exists() else 0
        }

        # Try to extract document-level metadata
        try:
            if hasattr(document, 'metadata'):
                doc_metadata = document.metadata
                if hasattr(doc_metadata, 'title') and doc_metadata.title:
                    metadata['title'] = doc_metadata.title
                if hasattr(doc_metadata, 'author') and doc_metadata.author:
                    metadata['author'] = doc_metadata.author
                if hasattr(doc_metadata, 'creation_date') and doc_metadata.creation_date:
                    metadata['creation_date'] = str(doc_metadata.creation_date)
        except Exception as e:
            self.logger.debug(f"Could not extract document metadata: {e}")

        return metadata

    def _extract_german_cities(self, text: str) -> List[str]:
        """
        Extract German city names from text.

        Args:
            text: Text to search

        Returns:
            List of detected city names
        """
        # Common German cities (add more as needed)
        german_cities = [
            'Berlin', 'Hamburg', 'München', 'Munich', 'Köln', 'Cologne',
            'Frankfurt', 'Stuttgart', 'Düsseldorf', 'Dortmund', 'Essen',
            'Leipzig', 'Bremen', 'Dresden', 'Hannover', 'Nürnberg', 'Nuremberg',
            'Duisburg', 'Bochum', 'Wuppertal', 'Bielefeld', 'Bonn', 'Münster',
            'Karlsruhe', 'Mannheim', 'Augsburg', 'Wiesbaden', 'Gelsenkirchen',
            'Mönchengladbach', 'Braunschweig', 'Chemnitz', 'Kiel', 'Aachen',
            'Halle', 'Magdeburg', 'Freiburg', 'Krefeld', 'Lübeck', 'Oberhausen',
            'Erfurt', 'Mainz', 'Rostock', 'Kassel', 'Hagen', 'Hamm', 'Saarbrücken',
            'Mülheim', 'Potsdam', 'Ludwigshafen', 'Oldenburg', 'Leverkusen',
            'Osnabrück', 'Solingen', 'Heidelberg', 'Herne', 'Neuss', 'Darmstadt',
            'Paderborn', 'Regensburg', 'Ingolstadt', 'Würzburg', 'Fürth',
            'Wolfsburg', 'Offenbach', 'Ulm', 'Heilbronn', 'Pforzheim', 'Göttingen',
            'Bottrop', 'Trier', 'Recklinghausen', 'Reutlingen', 'Bremerhaven',
            'Koblenz', 'Bergisch Gladbach', 'Jena', 'Remscheid', 'Erlangen',
            'Moers', 'Siegen', 'Hildesheim', 'Salzgitter'
        ]

        found_cities = []
        text_lower = text.lower()

        for city in german_cities:
            # Search for city name (case-insensitive)
            if city.lower() in text_lower:
                if city not in found_cities:
                    found_cities.append(city)

        return sorted(set(found_cities))

    def _extract_tables(self, document: Any) -> List[Dict[str, Any]]:
        """Extract tables from document."""
        tables = []

        try:
            # Docling provides tables as structured data
            if hasattr(document, 'tables'):
                for idx, table in enumerate(document.tables):
                    table_data = {
                        'index': idx,
                        'data': table.export_to_dataframe() if hasattr(table, 'export_to_dataframe') else str(table),
                        'page': getattr(table, 'page', 0)
                    }
                    tables.append(table_data)

        except Exception as e:
            self.logger.debug(f"Could not extract tables: {e}")

        return tables

    def _chunk_text(
        self,
        text: str,
        source_file: str,
        base_metadata: Dict[str, Any]
    ) -> List[PDFChunk]:
        """
        Split text into chunks with overlap.

        Args:
            text: Full document text
            source_file: Source filename
            base_metadata: Base metadata to include

        Returns:
            List of PDFChunk objects
        """
        chunks = []

        # Simple chunking by character count with overlap
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence or paragraph boundary
            if end < len(text):
                # Look for sentence end
                for delimiter in ['\n\n', '. ', '.\n', '\n']:
                    pos = text.rfind(delimiter, start, end)
                    if pos != -1:
                        end = pos + len(delimiter)
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:
                # Estimate page number (rough estimate)
                page_number = chunk_index // 2 + 1  # Assume ~2 chunks per page

                chunk = PDFChunk(
                    text=chunk_text,
                    page_number=page_number,
                    source_file=source_file,
                    chunk_index=chunk_index,
                    metadata=base_metadata.copy()
                )

                chunks.append(chunk)
                chunk_index += 1

            # Move start forward (with overlap)
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def _create_table_chunks(
        self,
        tables: List[Dict[str, Any]],
        source_file: str,
        base_metadata: Dict[str, Any]
    ) -> List[PDFChunk]:
        """Create chunks from extracted tables."""
        chunks = []

        for table in tables:
            # Convert table to text representation
            table_text = f"[TABLE {table['index']}]\n{str(table['data'])}"

            chunk = PDFChunk(
                text=table_text,
                page_number=table.get('page', 0),
                source_file=source_file,
                chunk_index=-1,  # Negative to distinguish from text chunks
                metadata={
                    **base_metadata,
                    'content_type': 'table',
                    'table_index': table['index']
                }
            )

            chunks.append(chunk)

        return chunks

    def process_directory(
        self,
        directory: Path,
        pattern: str = "*.pdf"
    ) -> Dict[str, List[PDFChunk]]:
        """
        Process all PDFs in a directory.

        Args:
            directory: Directory containing PDFs
            pattern: File pattern to match (default: *.pdf)

        Returns:
            Dict mapping filename to list of chunks
        """
        self.logger.info(f"Processing PDFs in directory: {directory}")

        results = {}
        pdf_files = list(Path(directory).glob(pattern))

        self.logger.info(f"Found {len(pdf_files)} PDF files")

        for pdf_path in pdf_files:
            try:
                chunks = self.process_pdf(pdf_path)
                results[pdf_path.name] = chunks
            except Exception as e:
                self.logger.error(f"Failed to process {pdf_path.name}: {e}")

        return results
