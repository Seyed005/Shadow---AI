from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse

from backend.gateway import (
    process_text,
    process_pdf,
    process_docx,
    process_xlsx,
    process_pptx,
    process_image,
    process_hitl_decision,
)

from backend.auth import (
    create_user,
    authenticate_user,
    create_auth_session,
    get_auth_session,
    delete_auth_session,
    get_user,
    get_user_by_email,
    create_password_reset_token,
    get_password_reset_user,
    delete_password_reset_token,
    update_password,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Shadow AI Security Gateway",
    version="1.0.0",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# CONFIGURATION
# ============================================================

AUTH_COOKIE_NAME = "shadow_ai_auth"
AUTH_COOKIE_MAX_AGE = 3600

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


# ============================================================
# AUTHENTICATION DEPENDENCY
# ============================================================

async def get_current_user(request: Request):
    """
    Validate the Shadow AI authentication cookie
    and return the authenticated user.
    """

    session_id = request.cookies.get(AUTH_COOKIE_NAME)

    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    session = await get_auth_session(session_id)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid.",
        )

    username = session.get("username")

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication session.",
        )

    user = await get_user(username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account not found.",
        )

    return user


# ============================================================
# FRONTEND ROUTES
# ============================================================

@app.get("/", include_in_schema=False)
async def root():
    """
    Authentication entry point.
    """

    login_page = FRONTEND_DIR / "login.html"

    if not login_page.exists():
        raise HTTPException(
            status_code=500,
            detail="Login page not found.",
        )

    return FileResponse(login_page)


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """
    Main Shadow AI dashboard.
    """

    dashboard_page = FRONTEND_DIR / "index.html"

    if not dashboard_page.exists():
        raise HTTPException(
            status_code=500,
            detail="Dashboard page not found.",
        )

    return FileResponse(dashboard_page)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Shadow AI Security Gateway",
        "version": "1.0.0",
    }


# ============================================================
# AUTH — SIGN UP
# ============================================================

@app.post("/auth/signup")
async def signup(
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    """
    Create a new normal Analyst account.
    """

    full_name = full_name.strip()
    username = username.strip()
    email = email.strip().lower()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Full name is required.",
        )

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required.",
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match.",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    existing_username = await get_user(username)

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )

    existing_email = await get_user_by_email(email)

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists.",
        )

    try:
        user = await create_user(
            full_name=full_name,
            username=username,
            email=email,
            password=password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "status": "SUCCESS",
        "message": "Account created successfully.",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "Analyst"),
        },
    }


# ============================================================
# AUTH — LOGIN
# ============================================================

@app.post("/auth/login")
async def login(
    response: Response,
    login: str = Form(...),
    password: str = Form(...),
):
    """
    Authenticate using username or email.
    """

    login = login.strip()

    if not login or not password:
        raise HTTPException(
            status_code=400,
            detail="Username/email and password are required.",
        )

    user = await authenticate_user(
        login=login,
        password=password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password.",
        )

    session_id = await create_auth_session(
        username=user["username"]
    )

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=session_id,
        max_age=AUTH_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return {
        "status": "SUCCESS",
        "message": "Login successful.",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "Analyst"),
        },
    }


# ============================================================
# AUTH — CURRENT USER
# ============================================================

@app.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    """
    Return the currently authenticated user.
    """

    return {
        "status": "SUCCESS",
        "authenticated": True,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "Analyst"),
        },
    }


# ============================================================
# AUTH — LOGOUT
# ============================================================

@app.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
):
    """
    Delete the authentication session and cookie.
    """

    session_id = request.cookies.get(AUTH_COOKIE_NAME)

    if session_id:
        await delete_auth_session(session_id)

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
    )

    return {
        "status": "SUCCESS",
        "message": "Logged out successfully.",
    }


# ============================================================
# AUTH — FORGOT PASSWORD
# ============================================================

@app.post("/auth/forgot-password")
async def forgot_password(
    email: str = Form(...),
):
    """
    Create a temporary password-reset token.

    For the Mini Project local/demo implementation,
    the token is returned directly.

    Production deployment should send the token
    through a verified email channel instead.
    """

    email = email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    user = await get_user_by_email(email)

    # Avoid revealing whether an account exists.
    if not user:
        return {
            "status": "SUCCESS",
            "message": (
                "If an account exists for this email, "
                "a password reset request has been created."
            ),
        }

    token = await create_password_reset_token(
        username=user["username"]
    )

    return {
        "status": "SUCCESS",
        "message": "Password reset token generated.",
        "reset_token": token,
        "expires_in": 900,
    }


# ============================================================
# AUTH — RESET PASSWORD
# ============================================================

@app.post("/auth/reset-password")
async def reset_password(
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    """
    Reset password using a valid temporary token.
    """

    token = token.strip()

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Reset token is required.",
        )

    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match.",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    username = await get_password_reset_user(token)

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token.",
        )

    updated = await update_password(
        username=username,
        new_password=password,
    )

    if not updated:
        raise HTTPException(
            status_code=400,
            detail="Unable to update password.",
        )

    await delete_password_reset_token(token)

    return {
        "status": "SUCCESS",
        "message": "Password reset successfully.",
    }


# ============================================================
# GATEWAY — TEXT SCAN
# ============================================================

@app.post("/gateway/scan")
async def gateway_scan(
    text: str = Form(...),
    session_id: str = Form(...),
    user=Depends(get_current_user),
):
    """
    Analyze a text request through the Shadow AI gateway.
    """

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    if not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID is required.",
        )

    try:
        result = await process_text(
            text=text,
            session_id=session_id,
        )

        return result

    except Exception as exc:
        print(f"Gateway scan error: {type(exc).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Gateway processing failed.",
        )


# ============================================================
# GATEWAY — HITL DECISION
# ============================================================

@app.post("/gateway/hitl")
async def gateway_hitl(
    session_id: str = Form(...),
    decision: str = Form(...),
    user=Depends(get_current_user),
):
    """
    Process the analyst's Human-in-the-Loop decision.
    """

    decision = decision.strip().upper()

    allowed_decisions = {
        "ALLOW",
        "SANITIZE_AND_SEND",
        "BLOCK",
    }

    if decision not in allowed_decisions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid decision. Use ALLOW, "
                "SANITIZE_AND_SEND, or BLOCK."
            ),
        )

    if not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID is required.",
        )

    try:
        result = await process_hitl_decision(
            session_id=session_id,
            decision=decision,
        )

        return result

    except Exception as exc:
        print(f"HITL processing error: {type(exc).__name__}")
        raise HTTPException(
            status_code=500,
            detail="HITL processing failed.",
        )


# ============================================================
# GATEWAY — FILE SCAN
# ============================================================

@app.post("/gateway/scan-file")
async def gateway_scan_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user=Depends(get_current_user),
):
    """
    Process PDF, DOCX, XLSX, PPTX, TXT and image inputs.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    if not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension or 'unknown'}"
            ),
        )

    temp_path = None

    try:
        suffix = extension

        with NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                temp_file.write(chunk)

        if extension == ".pdf":

            result = await process_pdf(
                temp_path,
                session_id,
            )

        elif extension == ".docx":

            result = await process_docx(
                temp_path,
                session_id,
            )

        elif extension == ".xlsx":

            result = await process_xlsx(
                temp_path,
                session_id,
            )

        elif extension == ".pptx":

            result = await process_pptx(
                temp_path,
                session_id,
            )

        elif extension == ".txt":

            with open(
                temp_path,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as text_file:
                text = text_file.read()

            result = await process_text(
                text=text,
                session_id=session_id,
            )

        elif extension in IMAGE_EXTENSIONS:

            result = await process_image(
                temp_path,
                session_id,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type.",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"File gateway error: "
            f"{type(exc).__name__}"
        )

        raise HTTPException(
            status_code=500,
            detail="File processing failed.",
        )

    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(
                    missing_ok=True
                )
            except Exception:
                pass