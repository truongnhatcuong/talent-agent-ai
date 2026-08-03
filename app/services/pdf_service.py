import fitz
import io
import docx

class PDFService:

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str = "document.pdf") -> str:
        """
        Đọc toàn bộ nội dung của file PDF, DOCX, DOC hoặc TXT từ bộ nhớ RAM
        """
        fn = filename.lower()
        if fn.endswith(".docx"):
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception as e:
                print(f"Error reading docx with python-docx: {e}")

        if fn.endswith(".txt"):
            try:
                return file_bytes.decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"Error reading txt: {e}")

        # Fallback for PDF or DOC/other files using PyMuPDF (fitz) or raw text extraction
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in document:
                text += page.get_text()
            document.close()
            if text.strip():
                return text
        except Exception:
            pass

        # Final fallback: decode bytes with utf-8
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""