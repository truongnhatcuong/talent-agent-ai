import fitz


class PDFService:

    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """
        Đọc toàn bộ nội dung của file PDF từ bộ nhớ RAM
        """

        document = fitz.open(stream=pdf_bytes, filetype="pdf")

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text