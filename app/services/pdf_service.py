import fitz
import io
import docx
import pytesseract
from pdf2image import convert_from_bytes

class PDFService:

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str = "document.pdf") -> str:
        """
        Đọc toàn bộ nội dung của file PDF, DOCX, DOC hoặc TXT từ bộ nhớ RAM
        """
        fn = filename.lower()
        if fn.endswith(".docx") or fn.endswith(".doc"):
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                if text.strip():
                    return text
            except Exception as e:
                print(f"Error reading docx with python-docx: {e}")

        if fn.endswith(".txt"):
            try:
                return file_bytes.decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"Error reading txt: {e}")

        # Phương án 1: Đọc PDF bằng PyMuPDF (fitz)
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in document:
                text += page.get_text()
            document.close()
            if text.strip():
                return text
        except Exception as e:
            print(f"Error reading PDF with PyMuPDF: {e}")

        # Phương án 2: Đọc PDF bằng PyPDF2 (Dự phòng)
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                return text
        except Exception as e:
            pass

        # Phương án 3: OCR nếu PDF hoặc file ảnh
        if fn.endswith(".pdf") or fn.endswith(".png") or fn.endswith(".jpg") or fn.endswith(".jpeg"):
            try:
                import platform
                import os
                from PIL import Image
                
                # Sửa lỗi Heroku không tìm thấy dữ liệu Tiếng Việt (TESSDATA_PREFIX)
                tess_paths = [
                    "/app/.apt/usr/share/tesseract-ocr/5/tessdata",
                    "/app/.apt/usr/share/tesseract-ocr/4.00/tessdata",
                    "/usr/share/tesseract-ocr/5/tessdata"
                ]
                for p in tess_paths:
                    if os.path.exists(p):
                        os.environ["TESSDATA_PREFIX"] = p
                        break
                
                if platform.system() == "Windows":
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                
                ocr_text = ""
                
                if fn.endswith(".pdf"):
                    if platform.system() == "Windows":
                        poppler_path = r'C:\poppler\Library\bin'
                        images = convert_from_bytes(file_bytes, poppler_path=poppler_path)
                    else:
                        images = convert_from_bytes(file_bytes)
                    for img in images:
                        ocr_text += pytesseract.image_to_string(img, lang='vie+eng') + "\n"
                else:
                    img = Image.open(io.BytesIO(file_bytes))
                    ocr_text = pytesseract.image_to_string(img, lang='vie+eng')
                
                if ocr_text.strip():
                    return ocr_text
            except Exception as e:
                print(f"Error reading with OCR: {e}")

        # Final fallback: chỉ áp dụng nếu là plain text thực sự
        try:
            decoded = file_bytes.decode("utf-8", errors="ignore")
            if "\x00" not in decoded[:1000] and len(decoded) < 50000:
                return decoded
        except Exception:
            pass

        return ""
