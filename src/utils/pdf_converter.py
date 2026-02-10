"""PDF to image conversion utility."""
import io
from typing import Optional, List
from pdf2image import convert_from_bytes
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFConverter:
    """Convert PDFs to images for Textract compatibility."""

    @staticmethod
    def is_pdf(document_bytes: bytes) -> bool:
        """Check if document is a PDF.

        Args:
            document_bytes: Document content as bytes

        Returns:
            bool: True if document is PDF
        """
        return document_bytes[:4] == b'%PDF'

    @staticmethod
    def convert_to_image(document_bytes: bytes, dpi: int = 300) -> Optional[bytes]:
        """Convert PDF to image format (PNG for single page).

        Args:
            document_bytes: PDF content as bytes
            dpi: Resolution for conversion (default 300)

        Returns:
            bytes: PNG image bytes of first page, or None if conversion fails
        """
        try:
            logger.info("Converting PDF to image format for Textract compatibility")
            
            # Convert PDF to images (one per page)
            images = convert_from_bytes(document_bytes, dpi=dpi, fmt='png')
            
            if not images:
                logger.error("PDF conversion produced no images")
                return None
            
            logger.info(f"PDF converted: {len(images)} page(s)")
            
            # Take first page
            first_page = images[0]
            logger.info(f"Image size: {first_page.size}, mode: {first_page.mode}")
            
            # Convert to PNG bytes
            img_buffer = io.BytesIO()
            first_page.save(img_buffer, format='PNG', optimize=True)
            img_bytes = img_buffer.getvalue()
            
            logger.info(f"Converted to PNG: {len(img_bytes) / 1024:.1f} KB")
            return img_bytes
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            logger.warning("Attempting to use original PDF with Textract anyway")
            return None

    @staticmethod
    def convert_all_pages_to_images(document_bytes: bytes, dpi: int = 300) -> List[bytes]:
        """Convert ALL pages of PDF to separate PNG images for Textract.

        Args:
            document_bytes: PDF content as bytes
            dpi: Resolution for conversion (default 300)

        Returns:
            List[bytes]: List of PNG image bytes (one per page)
        """
        try:
            logger.info("Converting PDF to multiple PNG images (one per page)")
            
            # Convert PDF to images (one per page)
            images = convert_from_bytes(document_bytes, dpi=dpi, fmt='png')
            
            if not images:
                logger.error("PDF conversion produced no images")
                return []
            
            logger.info(f"PDF converted: {len(images)} page(s)")
            
            # Convert each page to PNG bytes
            page_bytes_list = []
            for i, page_image in enumerate(images):
                img_buffer = io.BytesIO()
                page_image.save(img_buffer, format='PNG', optimize=True)
                page_bytes = img_buffer.getvalue()
                page_bytes_list.append(page_bytes)
                logger.info(f"  Page {i+1}: {len(page_bytes) / 1024:.1f} KB")
            
            logger.info(f"Successfully converted {len(page_bytes_list)} pages to PNG")
            return page_bytes_list
            
        except Exception as e:
            logger.error(f"Multi-page PDF conversion failed: {str(e)}")
            return []
