from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase
from app.schemas.interview import InterviewCreate, InterviewUpdate

router = APIRouter(
    prefix="/interviews",
    tags=["Interviews"]
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_interview(
    interview_in: InterviewCreate,
    supabase: Client = Depends(get_supabase)
):
    """
    Tạo lịch hẹn phỏng vấn mới và lưu vào Supabase DB.
    """
    payload = interview_in.model_dump()
    try:
        res = supabase.table("interview").insert(payload).execute()
        return res.data[0] if res.data else payload
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'interview' trên Supabase chưa mở quyền INSERT."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/")
async def list_interviews(supabase: Client = Depends(get_supabase)):
    """
    Lấy danh sách lịch phỏng vấn từ CSDL Supabase.
    """
    try:
        res = supabase.table("interview").select("*").order("id", desc=True).execute()
        return res.data
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/{interview_id}")
async def get_interview(interview_id: int, supabase: Client = Depends(get_supabase)):
    """
    Xem chi tiết 1 lịch phỏng vấn theo ID.
    """
    try:
        res = supabase.table("interview").select("*").eq("id", interview_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lịch phỏng vấn ID={interview_id}"
            )
        return res.data[0]
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.put("/{interview_id}")
async def update_interview(
    interview_id: int,
    interview_in: InterviewUpdate,
    supabase: Client = Depends(get_supabase)
):
    """
    Cập nhật trạng thái / đánh giá / ghi chú lịch phỏng vấn trong Supabase DB.
    """
    payload = {k: v for k, v in interview_in.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không có dữ liệu thay đổi.")

    try:
        res = supabase.table("interview").update(payload).eq("id", interview_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lịch phỏng vấn ID={interview_id}"
            )
        return res.data[0]
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.delete("/{interview_id}")
async def delete_interview(interview_id: int, supabase: Client = Depends(get_supabase)):
    """
    Xóa 1 lịch phỏng vấn khỏi Supabase CSDL.
    """
    try:
        res = supabase.table("interview").delete().eq("id", interview_id).execute()
        return {"message": f"Đã xóa thành công lịch phỏng vấn ID={interview_id}"}
    except APIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
