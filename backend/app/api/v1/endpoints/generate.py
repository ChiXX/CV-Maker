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
from .schemas import (
    JobExtractionRequest, JobExtractionResponse,
    CvGenerationResponse, ClGenerationResponse,
    JobApplicationResponse, CompilePdfRequest
)
from app.services.cv_generator import compile_cv_tex, wrap_cv_in_latex
from app.services.cl_generator import compile_cl_tex, wrap_cl_in_latex
from app.services.jd_generator import extract_jd_from_url_with_llm

router = APIRouter()

# Initialize OpenAI client (this should probably be moved to a core config/client module later)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    base_url=os.getenv("OPENAI_BASE_URL")
)

@router.post("/job_description", response_model=JobExtractionResponse)
async def generate_job_description(
    request: JobExtractionRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Extract job details from URL and create initial application record
    """
    # Check if URL already exists
    existing_application = db.query(Application).filter(Application.job_url == request.job_url).first()
    if existing_application:
        # Return existing application with warning message
        response_data = JobExtractionResponse.model_validate(existing_application)
        response_data.warning = "This job application already exists. Please check your applications list."
        return response_data

    try:
        # Extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, request.job_url)

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

@router.put("/{application_id}/job_description", response_model=JobExtractionResponse)
async def regenerate_job_description(
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
            # How to get raw content from existing latex? 
            # For simplicity, if it exists, the FE will just skip editing
            # But the response schema requires raw_content. 
            return CvGenerationResponse(raw_content="", plan_steps=None)

        # Generate raw CV summary
        raw_summary, plan_steps = compile_cv_tex(client, application.jd_text)
        
        return CvGenerationResponse(raw_content=raw_summary, plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV generation: {str(e)}")

@router.put("/{application_id}/cv", response_model=CvGenerationResponse)
async def regenerate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate CV raw summary
    """
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Generate raw CV summary
        raw_summary, plan_steps = compile_cv_tex(client, application.jd_text)

        return CvGenerationResponse(raw_content=raw_summary, plan_steps=plan_steps)
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
            return ClGenerationResponse(raw_content="", plan_steps=None)

        # Generate CL raw content
        raw_body, plan_steps = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        return ClGenerationResponse(raw_content=raw_body, plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")

@router.put("/{application_id}/cl", response_model=ClGenerationResponse)
async def regenerate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate cover letter raw content
    """
    try:
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        raw_body, plan_steps = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        return ClGenerationResponse(raw_content=raw_body, plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate cover letter: {str(e)}")


@router.post("/{application_id}/compile_pdf/{target}")
async def compile_pdf(
    application_id: int,
    target: str,
    request: Optional[CompilePdfRequest] = None,
    db: Session = Depends(get_db_dependency)
):
    """
    Compile PDF from content.
    If request.raw_content is provided, wraps it in LaTeX and saves to DB first.
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if target not in ['cv', 'cl']:
        raise HTTPException(status_code=400, detail="Target must be 'cv' or 'cl'")

    # If raw content is provided, wrap and save it
    if request and request.raw_content:
        if target == 'cv':
            latex_content = wrap_cv_in_latex(request.raw_content)
            application.cv_latex = latex_content
        else:
            latex_content = wrap_cl_in_latex(request.raw_content)
            application.cl_latex = latex_content
        
        db.commit()
        db.refresh(application)
    else:
        # Get existing LaTeX content
        latex_content = application.cv_latex if target == 'cv' else application.cl_latex
    
    if not latex_content:
        raise HTTPException(status_code=400, detail=f"No {target.upper()} content found and no raw_content provided")

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

            # Run xelatex (supports system fonts and is more modern)
            proc = subprocess.run([
                "xelatex",
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
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compilation failed: {str(e)}")
