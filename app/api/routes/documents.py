import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import RedirectResponse

from app.core.templates import templates
from app.db.session import SessionLocal
from app.models import Document
from app.services.rag import process_document
from app.utils.auth import get_current_user


router = APIRouter()


@router.get("/documents")
def documents(request: Request):
    db = SessionLocal()

    user = get_current_user(request)
    docs = db.query(Document).filter(Document.user == user).all()
    db.close()

    return templates.TemplateResponse(
        "documents.html",
        {"request": request, "docs": docs}
    )


@router.post("/documents/upload")
def upload_document(request: Request, file: UploadFile = File(...)):
    file_location = f"data/documents/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user = get_current_user(request)

    try:
        process_document(file_location)
    except Exception as e:
        print("PDF processing failed:", str(e))

    db = SessionLocal()
    doc = Document(
        name=file.filename,
        file_path=file_location,
        uploaded_date=datetime.now(timezone.utc).date(),
        user=user
    )
    db.add(doc)
    db.commit()
    db.close()

    return RedirectResponse(url="/documents", status_code=303)


@router.get("/documents/delete/{id}")
def delete_document(request: Request, id: int):
    db = SessionLocal()
    user = get_current_user(request)
    doc = db.query(Document).filter(
        Document.id == id,
        Document.user == user
    ).first()

    if not doc:
        db.close()
        return RedirectResponse("/documents")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    db.close()

    return RedirectResponse(url="/documents", status_code=303)
