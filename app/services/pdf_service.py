import fitz


class PDFService:

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """
        Đọc toàn bộ nội dung của file PDF
        """

        document = fitz.open(pdf_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text