"""
PDF Parser Module for SoF Event Extractor
Handles PDF text extraction using PyPDF2
"""

import PyPDF2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    """PDF text extraction utility"""
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
    
    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            if not text.strip():
                logger.warning(f"No text extracted from PDF: {file_path}")
                return ""
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def is_supported(self, file_path: Path) -> bool:
        """Check if file extension is supported"""
        return file_path.suffix.lower() in self.supported_extensions
