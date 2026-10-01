from pathlib import Path
import tempfile

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException
)

from backend.gateway import (
    process_text,
    process_pdf,
    process_docx,
    process_xlsx,
    process_pptx,
    process_image,
    process_hitl_decision
)


app = FastAPI(
    title="Shadow AI Security Gateway",
    version="1.0.0"
)


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
    ".webp"
}


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp"
}


@app.get("/")
async def root():
    return {
        "project": "Shadow AI Security Gateway",
        "status": "online"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/gateway/scan")
async def gateway_scan(
    text: str = Form(...),
    session_id: str = Form(...)
):
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text input cannot be empty."
        )

    if not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty."
        )

    try:
        result = await process_text(
            text=text,
            session_id=session_id
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.post("/gateway/hitl")
async def gateway_hitl(
    session_id: str = Form(...),
    decision: str = Form(...)
):
    if not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty."
        )

    decision = decision.upper().strip()

    allowed_decisions = {
        "ALLOW",
        "SANITIZE_AND_SEND",
        "BLOCK"
    }

    if decision not in allowed_decisions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid decision. Use "
                "ALLOW, SANITIZE_AND_SEND, or BLOCK."
            )
        )

    try:
        result = await process_hitl_decision(
            session_id=session_id,
            decision=decision
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.post("/gateway/scan-file")
async def gateway_scan_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing."
        )

    if not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty."
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Allowed types: "
                "PDF, DOCX, XLSX, PPTX, TXT, "
                "PNG, JPG, JPEG, BMP, TIF, TIFF, WEBP."
            )
        )

    temporary_file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temporary_file:

            content = await file.read()

            temporary_file.write(content)

            temporary_file_path = Path(
                temporary_file.name
            )

        if extension == ".pdf":

            result = await process_pdf(
                pdf_path=str(
                    temporary_file_path
                ),
                session_id=session_id
            )

        elif extension == ".docx":

            result = await process_docx(
                docx_path=str(
                    temporary_file_path
                ),
                session_id=session_id
            )

        elif extension == ".xlsx":

            result = await process_xlsx(
                xlsx_path=str(
                    temporary_file_path
                ),
                session_id=session_id
            )

        elif extension == ".pptx":

            result = await process_pptx(
                pptx_path=str(
                    temporary_file_path
                ),
                session_id=session_id
            )

        elif extension == ".txt":

            text_content = content.decode(
                "utf-8",
                errors="replace"
            )

            result = await process_text(
                text=text_content,
                session_id=session_id
            )

        elif extension in IMAGE_EXTENSIONS:

            result = await process_image(
                image_path=str(
                    temporary_file_path
                ),
                session_id=session_id
            )

        else:

            raise HTTPException(
                status_code=400,
                detail="Unsupported file type."
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    finally:

        if (
            temporary_file_path
            and temporary_file_path.exists()
        ):
            try:
                temporary_file_path.unlink()
            except OSError:
                pass