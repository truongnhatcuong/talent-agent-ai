from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase
from app.schemas.recruiter import MatchRequest, MatchCandidateRequest, MatchJobRequest
from app.services.recruiter_service import RecruiterService

router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter"]
)

service = RecruiterService()


@router.get("/candidates")
async def get_candidates(supabase: Client = Depends(get_supabase)):
    """
    Lấy danh sách tất cả ứng viên đã lưu trong Supabase DB.
    """
    try:
        res = supabase.table("candidate").select("*").order("id", desc=True).execute()
        return res.data or []
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'candidate' đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.get("/candidates/{candidate_id}")
async def get_candidate_by_id(candidate_id: int, supabase: Client = Depends(get_supabase)):
    """
    Lấy chi tiết 1 ứng viên theo ID từ Supabase DB.
    """
    try:
        res = supabase.table("candidate").select("*").eq("id", candidate_id).execute()
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'candidate' đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ứng viên")
    
    return res.data[0]


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: int, supabase: Client = Depends(get_supabase)):
    """
    Xóa 1 ứng viên theo ID khỏi Supabase DB.
    """
    try:
        res = supabase.table("candidate").delete().eq("id", candidate_id).execute()
        return {"status": "success", "message": f"Đã xóa ứng viên ID {candidate_id}", "data": res.data}
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'candidate' đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e


@router.post("/match")
async def match(request: MatchRequest):
    result = await service.match_cv(
        request.cv,
        request.jd
    )

    return result


@router.post("/match-candidate")
async def match_candidate(request: MatchCandidateRequest, supabase: Client = Depends(get_supabase)):
    try:
        res = supabase.table("candidate").select("*").eq("id", request.candidate_id).execute()
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'candidate' trên Supabase đang bật RLS. Hãy chạy: ALTER TABLE public.candidate DISABLE ROW LEVEL SECURITY;"
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    if not res.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên")

    candidate = res.data[0]
    result = await service.match_cv(candidate, request.jd)

    return {
        "candidate_id": candidate.get("id"),
        "candidate_name": candidate.get("name"),
        "match_result": result
    }


@router.post("/match-job")
async def match_job(request: MatchJobRequest, supabase: Client = Depends(get_supabase)):
    """
    So sánh độ phù hợp giữa một ứng viên trong Supabase DB và một JD đã tạo trong Supabase DB.
    Đồng thời cập nhật kết quả vào bản ghi ứng viên.
    """
    # 1. Lấy thông tin Candidate
    try:
        res_cand = supabase.table("candidate").select("*").eq("id", request.candidate_id).execute()
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'candidate' trên Supabase đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    if not res_cand.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên")
    candidate = res_cand.data[0]

    # 2. Lấy thông tin Job / JD
    try:
        res_job = supabase.table("job").select("*").eq("id", request.job_id).execute()
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'job' trên Supabase đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    if not res_job.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin tuyển dụng / JD")
    job = res_job.data[0]
    job_title = job.get("title")

    jd_full_text = f"Vị trí: {job_title}\nPhòng ban: {job.get('department') or 'N/A'}\nLoại HĐ: {job.get('employment_type') or 'N/A'}\nMô tả & Yêu cầu công việc:\n{job.get('description')}"

    result = await service.match_cv(candidate, jd_full_text)

    # 3. Tự động lưu/cập nhật vào CSDL Supabase
    score = result.get("overall_score")
    if score is not None:
        try:
            supabase.table("candidate").update({
                "matched_job": job_title,
                "score": score
            }).eq("id", candidate.get("id")).execute()
        except Exception as ex:
            print("Warning updating matched job in DB:", ex)

    return {
        "candidate_id": candidate.get("id"),
        "candidate_name": candidate.get("name"),
        "job_id": job.get("id"),
        "job_title": job_title,
        "match_result": result
    }


@router.get("/recommend-jobs/{candidate_id}")
async def recommend_jobs_for_candidate(candidate_id: int, supabase: Client = Depends(get_supabase)):
    """
    So sánh CV của ứng viên với TẤT CẢ các tin tuyển dụng đang mở trong DB,
    trả về danh sách 'Đề xuất vị trí phù hợp' và LƯU TRỰC TIẾP VÀO CSDL.
    """
    try:
        res_cand = supabase.table("candidate").select("*").eq("id", candidate_id).execute()
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'candidate' trên Supabase đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    if not res_cand.data:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ứng viên với ID={candidate_id}")

    candidate = res_cand.data[0]

    try:
        res_jobs = supabase.table("job").select("*").execute()
    except APIError as e:
        if e.code == "42501":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi RLS: Bảng 'job' trên Supabase đang bật RLS."
            ) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    if not res_jobs.data:
        return {
            "candidate_id": candidate.get("id"),
            "candidate_name": candidate.get("name"),
            "recommended_jobs": [],
            "message": "Chưa có tin tuyển dụng nào trong hệ thống."
        }

    recommendations = await service.recommend_jobs(candidate, res_jobs.data)

    # TỰ ĐỘNG LƯU VÀO CSDL SUPABASE
    if recommendations:
        top_match = recommendations[0]
        try:
            supabase.table("candidate").update({
                "matched_job": top_match.get("title"),
                "score": top_match.get("match_score"),
                "recommended_jobs": recommendations
            }).eq("id", candidate_id).execute()
        except Exception as ex:
            print("Warning saving recommendations to DB:", ex)

    return {
        "candidate_id": candidate.get("id"),
        "candidate_name": candidate.get("name"),
        "matched_job": recommendations[0].get("title") if recommendations else None,
        "score": recommendations[0].get("match_score") if recommendations else None,
        "recommended_jobs": recommendations
    }
