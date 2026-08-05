from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException, status
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.output_parser import OutputParser
from app.services.recruiter_service import RecruiterService

router = APIRouter(
    prefix="/upload",
    tags=["Upload & Match"]
)

llm = LLMService()
recruiter_service = RecruiterService()


@router.post("/upload-cv")
async def upload_cv(
    files: List[UploadFile] = File(...),
    job_id: Optional[int] = Form(None),
    jd: Optional[str] = Form(None),
    auto_recommend: Optional[bool] = Form(True),
    supabase: Client = Depends(get_supabase)
):
    """
    Luồng xử lý hoàn chỉnh cho HR:
    1. Upload nhiều file PDF CV -> AI bóc tách thông tin -> Tự động nạp vào Database (bảng 'candidate').
    2. Nếu truyền 'job_id' hoặc 'jd': Phân tích chi tiết độ phù hợp với JD đó.
    3. Tự động so sánh CV với TẤT CẢ các tin tuyển dụng đang mở trong DB và đề xuất danh sách vị trí phù hợp xếp theo % match score.
    4. TỰ ĐỘNG LƯU KẾT QUẢ PHÂN TÍCH (matched_job, score, recommended_jobs) VÀO CSDL SUPABASE.
    """
    if not files:
        return {"message": "Vui lòng chọn ít nhất 1 file PDF CV"}

    # BƯỚC 3 & 4 (Setup trước): Lấy thông tin Job và danh sách tất cả Jobs để tái sử dụng cho từng CV
    target_jd = None
    job_title_from_id = None
    job_info = None

    if job_id:
        try:
            job_res = supabase.table("job").select("*").eq("id", job_id).execute()
            if job_res.data:
                job_obj = job_res.data[0]
                job_title_from_id = job_obj.get("title")
                target_jd = f"Vị trí: {job_title_from_id}\nPhòng ban: {job_obj.get('department') or 'N/A'}\nMô tả & Yêu cầu công việc:\n{job_obj.get('description')}"
                job_info = {
                    "id": job_obj.get("id"),
                    "title": job_title_from_id
                }
        except APIError as e:
            if e.code == "42501":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Lỗi RLS: Bảng 'job' trên Supabase chưa tắt RLS."
                ) from e

    if not target_jd and jd and jd.strip():
        target_jd = jd.strip()

    all_jobs_data = []
    if auto_recommend:
        try:
            all_jobs_res = supabase.table("job").select("*").execute()
            if all_jobs_res.data:
                all_jobs_data = all_jobs_res.data
        except APIError as e:
            if e.code != "42501":
                print("Warning fetching jobs for recommendation:", e)

    results = []

    for file in files:
        file_response = {"filename": file.filename}

        if file.content_type != "application/pdf":
            file_response["status"] = "error"
            file_response["message"] = "Chỉ hỗ trợ định dạng file PDF"
            results.append(file_response)
            continue

        try:
            # BƯỚC 1: Extract text & AI bóc tách CV
            pdf_bytes = await file.read()
            cv_text = PDFService.extract_text(pdf_bytes, filename=file.filename or "cv.pdf")
            
            if not cv_text or not cv_text.strip():
                file_response["status"] = "error"
                file_response["message"] = "Không thể trích xuất được văn bản từ file CV đã chọn. Vui lòng kiểm tra lại file."
                results.append(file_response)
                continue

            # Giới hạn độ dài văn bản CV tối đa
            if len(cv_text) > 15000:
                cv_text = cv_text[:15000]

            json_cv_str = await llm.parse_cv(cv_text)
            candidate_data = OutputParser.parse_json(json_cv_str)

            exp_val = candidate_data.get("exp")
            if isinstance(exp_val, str):
                exp_val = exp_val.strip()

            if not exp_val or str(exp_val).lower() in ["null", "none", ""]:
                exp_list = candidate_data.get("experience")
                if isinstance(exp_list, list) and len(exp_list) > 0:
                    exp_val = f"{len(exp_list)} vị trí kinh nghiệm"
                else:
                    exp_val = "Kinh nghiệm thực tế"

            if str(exp_val).isdigit():
                exp_val = f"{exp_val} năm"

            # BƯỚC 2: Tự động lưu thông tin Ứng viên vào Database (bảng candidate)
            insert_payload = {
                "name": candidate_data.get("name") or "Chưa rõ",
                "email": candidate_data.get("email"),
                "phone": candidate_data.get("phone"),
                "address": candidate_data.get("address"),
                "summary": candidate_data.get("summary"),
                "exp": str(exp_val),
                "domain_industry": candidate_data.get("domain_industry") or [],
                "primary_roles": candidate_data.get("primary_roles") or [],
                "skills": candidate_data.get("skills") or [],
                "experience": candidate_data.get("experience") or [],
                "education": candidate_data.get("education") or [],
                "projects": candidate_data.get("projects") or [],
                "languages": candidate_data.get("languages") or [],
                "certifications": candidate_data.get("certifications") or [],
            }

            try:
                res = supabase.table("candidate").insert(insert_payload).execute()
                saved_candidate = res.data[0] if res.data else insert_payload
                candidate_id = saved_candidate.get("id")
                
                file_response["status"] = "success"
                file_response["message"] = "Upload CV và nạp dữ liệu thành công!"
                file_response["candidate"] = saved_candidate
                if job_info:
                    file_response["job_info"] = job_info

            except APIError as e:
                file_response["status"] = "error"
                file_response["message"] = f"Lỗi DB: {e.message}"
                if e.code == "42501":
                    file_response["message"] = "Lỗi RLS: Bảng 'candidate' trên Supabase chưa tắt RLS."
                results.append(file_response)
                continue

            # BƯỚC 3: Phân tích độ phù hợp với JD cụ thể (nếu có)
            if target_jd:
                match_result = await recruiter_service.match_cv(candidate_data, target_jd)
                file_response["match_result"] = match_result

            # BƯỚC 4: Tự động so sánh với TẤT CẢ các JD trong DB để đưa ra "Đề xuất vị trí phù hợp"
            recommended_jobs = []
            if auto_recommend and all_jobs_data:
                recommended_jobs = await recruiter_service.recommend_jobs(candidate_data, all_jobs_data)
                file_response["recommended_jobs"] = recommended_jobs

            # BƯỚC 5: TỰ ĐỘNG LƯU KẾT QUẢ AI VÀO DATABASE (Update bản ghi Candidate)
            if candidate_id:
                update_data = {}
                if recommended_jobs:
                    top_match = recommended_jobs[0]
                    update_data["matched_job"] = top_match.get("title")
                    update_data["score"] = top_match.get("match_score")
                    update_data["recommended_jobs"] = recommended_jobs
                elif file_response.get("match_result"):
                    match_res = file_response["match_result"]
                    update_data["matched_job"] = job_title_from_id or "Vị trí đã phân tích"
                    update_data["score"] = match_res.get("overall_score")

                if update_data:
                    try:
                        upd_res = supabase.table("candidate").update(update_data).eq("id", candidate_id).execute()
                        if upd_res.data:
                            file_response["candidate"] = upd_res.data[0]
                        else:
                            file_response["candidate"].update(update_data)
                    except Exception as ex:
                        print("Warning updating candidate match in DB:", ex)

        except Exception as e:
            file_response["status"] = "error"
            file_response["message"] = f"Lỗi không xác định: {str(e)}"
            
        results.append(file_response)

    return {
        "message": f"Đã xử lý {len(results)} file CV",
        "results": results
    }