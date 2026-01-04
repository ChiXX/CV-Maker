from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
import re
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
from cv_generator import compile_cv_tex
from cl_generator import compile_cl_tex
from cv_generator import Planner, Solver
from jd_generator import extract_jd_from_url_with_llm
from database import get_db_dependency, init_db, create_tables
from models import Application
from fastapi.responses import StreamingResponse
from fastapi import BackgroundTasks
import subprocess
import tempfile
import shutil
import io
from fastapi import Query


# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)

# Initialize FastAPI app
app = FastAPI(
    title="CV Maker API",
    description="API for generating customized CV and cover letters from job descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory generation status store: application_id -> status dict
generation_status: Dict[int, Dict] = {}
# Pydantic models for API
class JobApplicationRequest(BaseModel):
    job_url: str

class JobApplicationResponse(BaseModel):
    id: int
    job_url: str
    company: str
    title: str
    jd_text: str
    cv_latex: Optional[str]
    cl_latex: Optional[str]
    created_at: datetime
    updated_at: datetime

class JobExtractionRequest(BaseModel):
    job_url: str

class JobExtractionResponse(BaseModel):
    id: int
    job_url: str
    company: str
    title: str
    jd_text: str
    created_at: datetime
    updated_at: datetime

class CvGenerationRequest(BaseModel):
    application_id: int

class CvGenerationResponse(BaseModel):
    cv_latex: str
    plan_steps: Optional[List[str]] = None

class ClGenerationRequest(BaseModel):
    application_id: int
class ClGenerationResponse(BaseModel):
    cl_latex: str
    plan_steps: Optional[List[str]] = None



class PdfCompileResponse(BaseModel):
    detail: str

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/applications/extract", response_model=JobExtractionResponse)
async def extract_job_details(
    request: JobExtractionRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Extract job details from URL and create initial application record
    """
    try:
        # Check if URL already exists
        existing_application = db.query(Application).filter(Application.jb_url == request.job_url).first()
        if existing_application:
            # Return existing application instead of creating duplicate
            return JobExtractionResponse(
                id=existing_application.id,
                job_url=existing_application.jb_url,
                company=existing_application.company,
                title=existing_application.title,
                jd_text=existing_application.jd_text,
                created_at=existing_application.created_at,
                updated_at=existing_application.updated_at
            )

        # Extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, request.job_url)

        # Create output directory
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)


        # Create application record with only JD info
        application = Application(
            jb_url=request.job_url,
            jd_text=jd_text,
            company=company,
            title=title,
        )

        # Save to database
        db.add(application)
        db.commit()
        db.refresh(application)

        return JobExtractionResponse(
            id=application.id,
            job_url=application.jb_url,
            company=application.company,
            title=application.title,
            jd_text=application.jd_text,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract job details: {str(e)}")

@app.put("/applications/{application_id}/extract", response_model=JobExtractionResponse)
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
        jd_text, company, title = extract_jd_from_url_with_llm(client, application.jb_url)

        # Update output directory and file
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)

        # Save updated JD text (sanitize title for filesystem safety)
        import re as _re
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

        return JobExtractionResponse(
            id=application.id,
            job_url=application.jb_url,
            company=application.company,
            title=application.title,
            jd_text=application.jd_text,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate job details: {str(e)}")


 


@app.post("/applications/{application_id}/cv", response_model=CvGenerationResponse)
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

        # Build plan synchronously and return it immediately, then run solver in background
        planner = Planner(client)
        solver = Solver(client)
        plan_steps = planner.build_plan(application.jd_text, solver.resume_skills)

        # initialize progress store
        generation_status[application_id] = {
            "plan": plan_steps,
            "current": 0,
            "total": len(plan_steps),
            "state": "pending",
            "last_result": None,
            "error": None,
        }

        # schedule background execution
        def run_generation(app_id: int, jd_text: str):
            try:
                generation_status[app_id]["state"] = "running"

                def progress_cb(step_index, step_text, result_text):
                    generation_status[app_id]["current"] = step_index
                    generation_status[app_id]["last_result"] = result_text

                result_text = solver.execute_with_progress(plan_steps, application.jd_text, progress_callback=progress_cb)

                # After execution, update application record
                app_obj = db.query(Application).filter(Application.id == app_id).first()
                if app_obj:
                    # replace cvparagraph in template using compile_cv_tex to get full latex (reuse function)
                    tex_updated, new_summary, _ = compile_cv_tex(client, jd_text)
                    app_obj.cv_latex = tex_updated
                    db.commit()

                generation_status[app_id]["state"] = "completed"
            except Exception as e:
                generation_status[app_id]["state"] = "failed"
                generation_status[app_id]["error"] = str(e)

        # Use a background task to run generation so HTTP response returns quickly
        import threading
        t = threading.Thread(target=run_generation, args=(application_id, application.jd_text), daemon=True)
        t.start()

        return CvGenerationResponse(cv_latex="", plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV generation: {str(e)}")

@app.put("/applications/{application_id}/cv", response_model=CvGenerationResponse)
async def regenerate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate CV LaTeX for an existing application (starts background generation and returns plan)
    """
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        planner = Planner(client)
        solver = Solver(client)
        plan_steps = planner.build_plan(application.jd_text, solver.resume_skills)

        generation_status[application_id] = {
            "plan": plan_steps,
            "current": 0,
            "total": len(plan_steps),
            "state": "pending",
            "last_result": None,
            "error": None,
        }

        def run_generation(app_id: int, jd_text: str):
            try:
                generation_status[app_id]["state"] = "running"

                def progress_cb(step_index, step_text, result_text):
                    generation_status[app_id]["current"] = step_index
                    generation_status[app_id]["last_result"] = result_text

                result_text = solver.execute_with_progress(plan_steps, application.jd_text, progress_callback=progress_cb)

                app_obj = db.query(Application).filter(Application.id == app_id).first()
                if app_obj:
                    tex_updated, new_summary, _ = compile_cv_tex(client, jd_text)
                    app_obj.cv_latex = tex_updated
                    db.commit()

                generation_status[app_id]["state"] = "completed"
            except Exception as e:
                generation_status[app_id]["state"] = "failed"
                generation_status[app_id]["error"] = str(e)

        import threading
        t = threading.Thread(target=run_generation, args=(application_id, application.jd_text), daemon=True)
        t.start()

        return CvGenerationResponse(cv_latex="", plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV regeneration: {str(e)}")

@app.post("/applications/{application_id}/cl", response_model=ClGenerationResponse)
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

        planner = Planner(client)
        solver = Solver(client)
        plan_steps = planner.build_plan(application.jd_text, application.cv_latex)

        generation_status[application_id] = {
            "plan": plan_steps,
            "current": 0,
            "total": len(plan_steps),
            "state": "pending",
            "last_result": None,
            "error": None,
        }

        def run_cl_generation(app_id: int, jd_text: str, company: str, title: str, cv_latex: str):
            try:
                generation_status[app_id]["state"] = "running"

                def progress_cb(step_index, step_text, result_text):
                    generation_status[app_id]["current"] = step_index
                    generation_status[app_id]["last_result"] = result_text

                result_text = solver.execute_with_progress(plan_steps, application.jd_text, progress_callback=progress_cb)

                app_obj = db.query(Application).filter(Application.id == app_id).first()
                if app_obj:
                    new_tex, letter_body, _ = compile_cl_tex(client, jd_text, company, title, cv_latex)
                    app_obj.cl_latex = new_tex
                    db.commit()

                generation_status[app_id]["state"] = "completed"
            except Exception as e:
                generation_status[app_id]["state"] = "failed"
                generation_status[app_id]["error"] = str(e)

        import threading
        t = threading.Thread(target=run_cl_generation, args=(application_id, application.jd_text, application.company, application.title, application.cv_latex), daemon=True)
        t.start()

        return ClGenerationResponse(cl_latex="", plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")

@app.put("/applications/{application_id}/cl", response_model=ClGenerationResponse)
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


@app.post("/applications/{application_id}/compile_pdf/{target}")
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
    import re as _re
    safe_company = _re.sub(r'[\\/:"*?<>|]+', '_', application.company)
    safe_title = _re.sub(r'[\\/:"*?<>|]+', '_', application.title)
    filename = f"{target}_{safe_company}_{safe_title}.pdf"

    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write LaTeX content to main.tex
            # Copy local LaTeX asset directories into the temp dir so pdflatex can find .cls, images, etc.
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
                                    # ignore individual copy errors
                                    pass
            except Exception as e:
                print(f"Warning: failed to copy LaTeX assets: {e}")

            tex_path = os.path.join(tmpdir, "main.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Run pdflatex to compile PDF (allow errors but continue)
            proc = subprocess.run([
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={tmpdir}",
                "main.tex",
            ], capture_output=True, text=True, cwd=tmpdir)

            pdf_path = os.path.join(tmpdir, "main.pdf")

            # Debug logging
            print(f"pdflatex return code: {proc.returncode}")
            print(f"pdflatex stdout: {proc.stdout[:500]}...")  # First 500 chars
            print(f"pdflatex stderr: {proc.stderr[:500]}...")  # First 500 chars
            print(f"Temporary directory: {tmpdir}")
            print(f"Files in temp dir: {os.listdir(tmpdir)}")

            # Check if PDF was generated, even if there were warnings/errors
            if not os.path.exists(pdf_path):
                # Collect full debug information
                files_in_tmp = os.listdir(tmpdir)
                error_info = {
                    "message": "PDF file was not generated",
                    "return_code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "temp_dir": tmpdir,
                    "files_in_temp_dir": files_in_tmp,
                }
                # Also save the .log and .tex contents if available for offline inspection
                try:
                    saved_debug_dir = os.path.join("Applications", "pdflatex_debug")
                    os.makedirs(saved_debug_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    debug_file = os.path.join(saved_debug_dir, f"debug-{application_id}-{timestamp}.json")
                    import json
                    with open(debug_file, "w", encoding="utf-8") as df:
                        json.dump(error_info, df, ensure_ascii=False, indent=2)
                    error_info["saved_debug_file"] = debug_file
                except Exception as e:
                    # ignore saving errors but note them
                    error_info["save_error"] = str(e)

                raise HTTPException(status_code=500, detail=error_info)

            # Read the PDF into memory before leaving the tempdir, to avoid the
            # TemporaryDirectory being removed before the response generator runs.
            try:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading generated PDF: {str(e)}")

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compilation failed: {str(e)}")


@app.get("/applications/{application_id}/progress")
async def get_generation_progress(application_id: int):
    """Return plan and progress for a given application"""
    status = generation_status.get(application_id)
    # Log a concise progress line so only this endpoint produces console output
    try:
        progress_logger.info("progress id=%s state=%s current=%s total=%s", application_id, status["state"] if status else "not_started", status["current"] if status else 0, status["total"] if status else 0)
    except Exception:
        pass
    if not status:
        # Return a harmless "not_started" status instead of 404 so polling clients
        # don't generate noisy 404 logs while waiting for generation to begin.
        return {
            "plan": [],
            "current": 0,
            "total": 0,
            "state": "not_started",
            "last_result": None,
            "error": None,
        }
    return status





@app.get("/test_pdflatex")
async def test_pdflatex():
    """
    Test endpoint to check pdflatex installation and basic functionality
    """
    try:
        # Test pdflatex version
        proc = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)
        version_info = proc.stdout.split('\n')[0] if proc.stdout else "No version info"

        # Create a minimal LaTeX document for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_content = r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
"""
            tex_path = os.path.join(tmpdir, "test.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(tex_content)

            # Try to compile
            proc = subprocess.run([
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={tmpdir}",
                "test.tex",
            ], capture_output=True, text=True, cwd=tmpdir, timeout=30)

            pdf_path = os.path.join(tmpdir, "test.pdf")
            pdf_exists = os.path.exists(pdf_path)

            return {
                "pdflatex_available": True,
                "version": version_info,
                "test_compilation": {
                    "return_code": proc.returncode,
                    "pdf_generated": pdf_exists,
                    "stdout_preview": proc.stdout[:200] + "..." if len(proc.stdout) > 200 else proc.stdout,
                    "stderr_preview": proc.stderr[:200] + "..." if len(proc.stderr) > 200 else proc.stderr,
                    "files_created": os.listdir(tmpdir)
                }
            }

    except subprocess.TimeoutExpired:
        return {"error": "pdflatex timed out"}
    except FileNotFoundError:
        return {"error": "pdflatex not found in PATH"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "CV Maker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

def main():
    """Main entry point for running the FastAPI server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
