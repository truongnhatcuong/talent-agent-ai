import json
from pathlib import Path
import shutil
from fastapi import APIRouter, File, UploadFile
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.output_parser import OutputParser
router = APIRouter(
     prefix="/upload",
    tags=["Upload"]
)
llm = LLMService()

@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    if not file:
        return {
            "message": "Vui lòng chọn file upload"
        }
    if file.content_type != "application/pdf":
        return {
            "message": "Chỉ hỗ trợ file PDF"
        }
    pdf_bytes = await file.read()
    cv_text = PDFService.extract_text(pdf_bytes)
    json_cv_str = await llm.parse_cv(cv_text)
    
    candidate_data = OutputParser.parse_json(json_cv_str)

    return {
        "message": "Upload thành công",
        "candidate": candidate_data
    }