"""
PDF Text Extraction Service
═════════════════════════════════════════════════════════════════════════════
Extracts text from uploaded PDF files using PyMuPDF (fitz) for best quality.
Falls back to pdfplumber for complex layouts.
"""
import io
from typing import Optional


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF (fitz).
    PyMuPDF is the fastest and most accurate extractor for text-based PDFs.
    
    Args:
        pdf_bytes: Raw PDF file bytes
    
    Returns:
        Extracted text string
    """
    try:
        import fitz  # PyMuPDF

        # Use context manager to ensure proper resource cleanup
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text_parts = []
            total_pages = len(doc)

            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    page_text = page.get_text("text")
                    if page_text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{page_text.strip()}")
                except Exception as page_err:
                    print(f"   ⚠️ [PDF] Failed to extract page {page_num + 1}: {page_err}")
                    continue

            full_text = "\n\n".join(text_parts)

            if full_text.strip():
                print(f"   📄 [PDF] Extracted {len(full_text)} chars via PyMuPDF from {total_pages} pages")
                return full_text.strip()

    except ImportError:
        print("   ⚠️ [PDF] PyMuPDF not installed, trying pdfplumber...")
    except Exception as e:
        print(f"   ⚠️ [PDF] PyMuPDF extraction failed: {e}, trying pdfplumber...")

    # Fallback: pdfplumber
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text.strip()}")

        full_text = "\n\n".join(text_parts)
        print(f"   📄 [PDF] Extracted {len(full_text)} chars via pdfplumber")
        return full_text.strip()

    except ImportError:
        raise RuntimeError(
            "No PDF extraction library available. Install PyMuPDF: pip install PyMuPDF"
        )
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {str(e)}")
