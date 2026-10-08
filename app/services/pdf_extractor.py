from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfExtractionError(ValueError):
    """Raised when resume text cannot be extracted from the uploaded PDF."""


def extract_resume_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        if reader.is_encrypted:
            raise PdfExtractionError("Password-protected PDFs are not supported.")
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except PdfExtractionError:
        raise
    except (PdfReadError, OSError, ValueError) as exc:
        raise PdfExtractionError("The uploaded file could not be read as a PDF.") from exc

    if not text:
        raise PdfExtractionError(
            "No selectable text was found in the PDF. Scanned-image OCR is not implemented."
        )

    return text
