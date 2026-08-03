from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase
from app.schemas.job import JobCreate, JobUpdate
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.services.output_parser import OutputParser

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs / JDs"]
)

llm_service = LLMService()


@router.post("/parse-jd-file")
async def parse_jd_file(file: UploadFile = File(...)):
    """
    Nhận file JD (PDF, DOCX, DOC, TXT), tự động trích xuất nội dung và dùng AI bóc tách thông tin tin tuyển dụng.
    """
    if not file:
        raise HTTPException(status_code=400, detail="Vui lòng chọn file văn bản JD")
    
    file_bytes = await file.read()
    raw_text = PDFService.extract_text(file_bytes, filename=file.filename or "jd.pdf")

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="Không thể trích xuất văn bản từ file JD đã chọn.")

    try:
        json_str = await llm_service.parse_jd(raw_text)
        parsed_data = OutputParser.parse_json(json_str)
    except Exception as e:
        print(f"AI JD parse error: {e}")
        parsed_data = {
            "title": file.filename.rsplit(".", 1)[0] if file.filename else "Vị trí tuyển dụng",
            "description": raw_text
        }

    if not parsed_data.get("description"):
        parsed_data["description"] = raw_text

    return {
        "success": True,
        "filename": file.filename,
        "raw_text": raw_text,
        "parsed": parsed_data
    }




@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(job_in: JobCreate, supabase: Client = Depends(get_supabase)):
    """
    Tạo tin tuyển dụng / JD mới và lưu vào cơ sở dữ liệu Supabase.
    """
    payload = job_in.model_dump()
    try:
        res = supabase.table("job").insert(payload).execute()
        return res.data[0] if res.data else payload
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS (Row Level Security): Bảng 'job' trên Supabase chưa tắt RLS hoặc chưa mở quyền INSERT. Hãy chạy SQL: ALTER TABLE public.job DISABLE ROW LEVEL SECURITY;"
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/")
async def list_jobs(supabase: Client = Depends(get_supabase)):
    """
    Lấy danh sách tất cả tin tuyển dụng / JD từ Supabase.
    """
    try:
        res = supabase.table("job").select("*").order("id", desc=True).execute()
        return res.data
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'job' trên Supabase đang bật Row Level Security."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/{job_id}")
async def get_job(job_id: int, supabase: Client = Depends(get_supabase)):
    """
    Xem thông tin chi tiết một tin tuyển dụng / JD theo ID từ Supabase.
    """
    try:
        res = supabase.table("job").select("*").eq("id", job_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy tin tuyển dụng với ID={job_id}"
            )
        return res.data[0]
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.delete("/{job_id}")
async def delete_job(job_id: int, supabase: Client = Depends(get_supabase)):
    """
    Xóa một tin tuyển dụng / JD khỏi cơ sở dữ liệu Supabase.
    """
    try:
        res = supabase.table("job").delete().eq("id", job_id).execute()
        return {"message": f"Đã xóa thành công tin tuyển dụng ID={job_id}"}
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.put("/{job_id}")
async def update_job(
    job_id: int,
    job_in: JobUpdate,
    supabase: Client = Depends(get_supabase)
):
    """
    Cập nhật thông tin chi tiết một tin tuyển dụng / JD trong CSDL Supabase.
    """
    payload = {k: v for k, v in job_in.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không có dữ liệu thay đổi.")

    try:
        res = supabase.table("job").update(payload).eq("id", job_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy tin tuyển dụng với ID={job_id}"
            )
        return res.data[0]
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

