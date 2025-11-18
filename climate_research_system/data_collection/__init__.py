"""
Data Collection Module

Components for collecting climate data from various sources including PDFs.
"""

from .document_store import DocumentStore, get_document_store
from .pdf_processor import PDFProcessor, PDFChunk
from .rag_retriever import RAGRetriever, RetrievalResult, get_rag_retriever

__all__ = [
    'DocumentStore',
    'get_document_store',
    'PDFProcessor',
    'PDFChunk',
    'RAGRetriever',
    'RetrievalResult',
    'get_rag_retriever',
]
