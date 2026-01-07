from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import shutil
import io
import subprocess
from datetime import datetime
import json
import re as _re

from openai import OpenAI
from app.db.session import get_db_dependency
from app.db.models import Application
from app.schemas.application import (
    JobExtractionRequest, JobExtractionResponse,
    CvGenerationResponse, ClGenerationResponse,
    JobApplicationResponse
)
from app.services.cv_generator import compile_cv_tex
from app.services.cl_generator import compile_cl_tex
from app.services.jd_generator import extract_jd_from_url_with_llm

router = APIRouter()

# Initialize OpenAI client (this should probably be moved to a core config/client module later)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    base_url=os.getenv("OPENAI_BASE_URL")
)

@router.post("/extract", response_model=JobExtractionResponse)
async def extract_job_details(
    request: JobExtractionRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Extract job details from URL and create initial application record
    """
    try:
        # Check if URL already exists
        existing_application = db.query(Application).filter(Application.job_url == request.job_url).first()
        if existing_application:
            # Return existing application instead of creating duplicate
            return existing_application

        # Extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, request.job_url)

        # Create output directory
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)

        # Create application record with only JD info
        application = Application(
            job_url=request.job_url,
            jd_text=jd_text,
            company=company,
            title=title,
        )

        # Save to database
        db.add(application)
        db.commit()
        db.refresh(application)

        return application

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract job details: {str(e)}")

@router.put("/{application_id}/extract", response_model=JobExtractionResponse)
async def regenerate_job_details(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate job details for an existing application
    """
    try:
        # Get existing application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Re-extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, application.job_url)

        # Update output directory and file
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)

        # Save updated JD text (sanitize title for filesystem safety)
        safe_title = _re.sub(r'[\\/:"*?<>|]+', '_', title)
        jd_txt_path = os.path.join(out_dir, f"{safe_title}.txt")
        os.makedirs(os.path.dirname(jd_txt_path), exist_ok=True)
        with open(jd_txt_path, "w", encoding="utf-8") as f:
            f.write(jd_text)

        # Update application record
        application.jd_text = jd_text
        application.company = company
        application.title = title
        # Clear CV and CL since JD changed
        application.cv_latex = None
        application.cl_latex = None

        db.commit()
        db.refresh(application)

        return application

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate job details: {str(e)}")


@router.post("/{application_id}/cv", response_model=CvGenerationResponse)
async def generate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Generate CV LaTeX for an existing application
    """
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Check if CV already exists
        if application.cv_latex:
            return CvGenerationResponse(cv_latex=application.cv_latex, plan_steps=None)

        # Generate CV LaTeX directly
        cv_latex, new_summary, plan_steps = compile_cv_tex(client, application.jd_text)
        # Update application
        application.cv_latex = cv_latex
        db.commit()

        return CvGenerationResponse(cv_latex=cv_latex, plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV generation: {str(e)}")

@router.put("/{application_id}/cv", response_model=CvGenerationResponse)
async def regenerate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate CV LaTeX for an existing application
    """
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Generate CV LaTeX directly
        cv_latex, new_summary, plan_steps = compile_cv_tex(client, application.jd_text)

        # Update application
        application.cv_latex = cv_latex
        db.commit()

        return CvGenerationResponse(cv_latex=cv_latex, plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV regeneration: {str(e)}")

@router.post("/{application_id}/cl", response_model=ClGenerationResponse)
async def generate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Generate cover letter LaTeX for an existing application
    """
    try:
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Check if CL already exists
        if application.cl_latex:
            return ClGenerationResponse(cl_latex=application.cl_latex, plan_steps=None)

        # Generate CL LaTeX directly
        cl_latex, letter_body, plan_steps = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        # Update application
        application.cl_latex = cl_latex
        db.commit()

        return ClGenerationResponse(cl_latex=cl_latex, plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")

@router.put("/{application_id}/cl", response_model=ClGenerationResponse)
async def regenerate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate cover letter LaTeX for an existing application
    """
    try:
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Regenerate CL LaTeX and obtain plan steps
        cl_latex, _, plan_steps = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        # Update application
        application.cl_latex = cl_latex
        db.commit()

        return ClGenerationResponse(cl_latex=cl_latex, plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate cover letter: {str(e)}")


@router.post("/{application_id}/compile_pdf/{target}")
async def compile_pdf(
    application_id: int,
    target: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Compile PDF from LaTeX content using pdflatex
    target: 'cv' or 'cl' (CV or Cover Letter)
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if target not in ['cv', 'cl']:
        raise HTTPException(status_code=400, detail="Target must be 'cv' or 'cl'")

    # Get LaTeX content
    latex_content = application.cv_latex if target == 'cv' else application.cl_latex
    if not latex_content:
        raise HTTPException(status_code=400, detail=f"No {target.upper()} content found")

    # Sanitize filename for Content-Disposition header
    safe_company = _re.sub(r'[\\/:"*?<>|]+', '_', application.company)
    safe_title = _re.sub(r'[\\/:"*?<>|]+', '_', application.title)
    filename = f"{target}_{safe_company}_{safe_title}.pdf"

    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy local LaTeX asset directories 
            try:
                project_root = os.getcwd()
                for src_dir in ["latex_cv", "latex_cl"]:
                    src_path = os.path.join(project_root, src_dir)
                    if os.path.exists(src_path) and os.path.isdir(src_path):
                        for root_dir, dirs, files in os.walk(src_path):
                            rel_root = os.path.relpath(root_dir, src_path)
                            dest_root = tmpdir if rel_root == "." else os.path.join(tmpdir, rel_root)
                            os.makedirs(dest_root, exist_ok=True)
                            for fname in files:
                                try:
                                    shutil.copy2(os.path.join(root_dir, fname), os.path.join(dest_root, fname))
                                except Exception:
                                    pass
            except Exception as e:
                print(f"Warning: failed to copy LaTeX assets: {e}")

            tex_path = os.path.join(tmpdir, "main.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Run pdflatex
            proc = subprocess.run([
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={tmpdir}",
                "main.tex",
            ], capture_output=True, text=True, cwd=tmpdir)

            pdf_path = os.path.join(tmpdir, "main.pdf")

            if not os.path.exists(pdf_path):
                # Collect full debug information
                files_in_tmp = os.listdir(tmpdir)
                error_info = {
                    "message": "PDF file was not generated",
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "files_in_temp_dir": files_in_tmp,
                }
                raise HTTPException(status_code=500, detail=error_info)

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compilation failed: {str(e)}")

@router.get("", response_model=List[JobApplicationResponse])
async def list_applications(
    db: Session = Depends(get_db_dependency)
):
    """
    List all applications
    """
    applications = db.query(Application).order_by(Application.created_at.desc()).all()
    return applications

@router.get("/{application_id}", response_model=JobApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get a single application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Delete an application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"detail": "Application deleted successfully"}
