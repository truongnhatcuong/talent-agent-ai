from app.core.config import GOOGLE_DOC_ID
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
import urllib.request
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from postgrest.exceptions import APIError

from app.core.database import get_supabase
from app.core.config import EMAIL_USER, EMAIL_PASS
from app.schemas.recruiter import MatchRequest, MatchCandidateRequest, MatchJobRequest, SendEmailRequest
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


@router.get("/candidates/test-email")
async def test_email_sending():
    """
    Test gửi email trực tiếp qua Gmail SMTP bằng đường dẫn trình duyệt
    """
    clean_user = str(EMAIL_USER).strip() if EMAIL_USER else "truongnhatcuong2222004@gmail.com"
    clean_pass = str(EMAIL_PASS).replace(" ", "").replace("-", "").strip() if EMAIL_PASS else ""

    msg = MIMEMultipart()
    msg["From"] = f"Talent Agent AI <{clean_user}>"
    msg["To"] = clean_user
    msg["Subject"] = "[Talent Agent AI] Test Gửi Email SMTP Thành Công"
    msg.attach(MIMEText("Xin chào, đây là email kiểm tra hệ thống Talent Agent AI!", "plain", "utf-8"))

    # Thử Cổng 587
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, local_hostname="localhost", timeout=15) as server:
            server.starttls()
            server.login(clean_user, clean_pass)
            server.send_message(msg)
            return {
                "status": "success",
                "port": 587,
                "email_user": clean_user,
                "message": f"Gửi email test thực tế thành công tới {clean_user} qua Cổng 587!"
            }
    except Exception as e587:
        print("Port 587 test failed:", e587)

    # Thử Cổng 465 SSL
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, local_hostname="localhost", context=context, timeout=15) as server:
            server.login(clean_user, clean_pass)
            server.send_message(msg)
            return {
                "status": "success",
                "port": 465,
                "email_user": clean_user,
                "message": f"Gửi email test thực tế thành công tới {clean_user} qua Cổng 465 SSL!"
            }
    except Exception as e465:
        print("Port 465 test failed:", e465)

    return {
        "status": "error",
        "email_user": clean_user,
        "message": "Không thể kết nối máy chủ gửi mail."
    }


@router.post("/candidates/send-email")
async def send_candidate_email(req: SendEmailRequest):
    """
    Gửi email trực tiếp cho ứng viên bằng SMTP Gmail
    """

    clean_user = str(EMAIL_USER).strip() if EMAIL_USER else "truongnhatcuong2222004@gmail.com"
    clean_pass = str(EMAIL_PASS).replace(" ", "").replace("-", "").strip() if EMAIL_PASS else ""

    msg = MIMEMultipart()
    msg["From"] = f"Talent Agent AI <{clean_user}>"
    msg["To"] = req.to_email
    msg["Subject"] = req.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    msg.attach(MIMEText(req.body, "plain", "utf-8"))

    # Cách 1: Thử Cổng 587
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, local_hostname="localhost", timeout=15) as server:
            server.starttls()
            server.login(clean_user, clean_pass)
            server.send_message(msg)
            return {"status": "success", "message": f"Đã gửi email thực tế thành công tới {req.to_email} qua Gmail SMTP Cổng 587!"}
    except smtplib.SMTPAuthenticationError as auth_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu ứng dụng Gmail (EMAIL_PASS) không chính xác."
        ) from auth_err
    except Exception as e:
        print("Port 587 failed:", e)

    # Cách 2: Thử Cổng 465 SSL
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, local_hostname="localhost", context=context, timeout=15) as server:
            server.login(clean_user, clean_pass)
            server.send_message(msg)
            return {"status": "success", "message": f"Đã gửi email thực tế thành công tới {req.to_email} qua Gmail SMTP Cổng 465 SSL!"}
    except smtplib.SMTPAuthenticationError as auth_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu ứng dụng Gmail (EMAIL_PASS) không chính xác."
        ) from auth_err
    except Exception as e:
        print("Port 465 failed:", e)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Không thể gửi email qua Gmail SMTP."
    )


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


@router.post("/candidates/send-email")
async def send_candidate_email(req: SendEmailRequest):
    """
    Gửi email trực tiếp cho ứng viên bằng SMTP Gmail
    """
    if not EMAIL_USER or not EMAIL_PASS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chưa cấu hình EMAIL_USER hoặc EMAIL_PASS trong file .env"
        )

    clean_user = str(EMAIL_USER).strip()
    # Bắt buộc xóa khoảng trắng trong Mật khẩu ứng dụng 16 ký tự của Gmail
    clean_pass = str(EMAIL_PASS).replace(" ", "").replace("-", "").strip()

    msg = MIMEMultipart()
    msg["From"] = f"Talent Agent AI <{clean_user}>"
    msg["To"] = req.to_email
    msg["Subject"] = req.subject
    msg.attach(MIMEText(req.body, "plain", "utf-8"))

    last_error = None

    # Cách 1: Thử Cổng 587 với STARTTLS
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(clean_user, clean_pass)
            server.send_message(msg)
            return {"status": "success", "message": f"Email đã gửi thành công tới {req.to_email}"}
    except smtplib.SMTPAuthenticationError as auth_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu ứng dụng Gmail (EMAIL_PASS) không chính xác. Vui lòng kiểm tra Mật khẩu ứng dụng 16 ký tự tại Google Account."
        ) from auth_err
    except Exception as e:
        last_error = e

    # Cách 2: Fallback Cổng 465 với SSL trực tiếp
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as server:
            server.login(clean_user, clean_pass)
            server.send_message(msg)
            return {"status": "success", "message": f"Email đã gửi thành công tới {req.to_email}"}
    except smtplib.SMTPAuthenticationError as auth_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu ứng dụng Gmail (EMAIL_PASS) không chính xác. Vui lòng kiểm tra Mật khẩu ứng dụng 16 ký tự tại Google Account."
        ) from auth_err
    except Exception as e:
        last_error = e

    print(f"Error sending email via SMTP: {last_error}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Lỗi khi gửi email: {str(last_error)}"
    )


@router.get("/email-template")
async def get_email_template():
    """
    Proxy để lấy nội dung text từ Google Docs để tránh lỗi CORS ở trình duyệt.
    """
    url = f"https://docs.google.com/document/d/{GOOGLE_DOC_ID}/export?format=txt"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            return {"template": content}
    except urllib.error.URLError as e:
        raise HTTPException(status_code=500, detail=f"Không thể tải mẫu thư: {str(e)}")

