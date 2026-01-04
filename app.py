from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import re
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
from cv_generator import compile_cv_tex
from cl_generator import compile_cl_tex
from jd_generator import extract_jd_from_url_with_llm
from database import get_db_dependency, init_db, create_tables
from models import Application
from fastapi.responses import StreamingResponse
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

class ClGenerationRequest(BaseModel):
    application_id: int

class ClGenerationResponse(BaseModel):
    cl_latex: str

class ApplicationListResponse(BaseModel):
    applications: List[JobApplicationResponse]


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
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Generate CV LaTeX
        cv_latex, _ = compile_cv_tex(client, application.jd_text)

        # Update application
        application.cv_latex = cv_latex
        db.commit()

        return CvGenerationResponse(cv_latex=cv_latex)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CV: {str(e)}")

@app.put("/applications/{application_id}/cv", response_model=CvGenerationResponse)
async def regenerate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate CV LaTeX for an existing application
    """
    try:
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Regenerate CV LaTeX
        cv_latex = compile_cv_tex(client, application.jd_text)

        # Update application
        application.cv_latex = cv_latex
        db.commit()

        return CvGenerationResponse(cv_latex=cv_latex)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate CV: {str(e)}")

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

        # Generate CL LaTeX
        cl_latex, _ = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        # Update application
        application.cl_latex = cl_latex
        db.commit()

        return ClGenerationResponse(cl_latex=cl_latex)

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

        # Regenerate CL LaTeX
        cl_latex, _ = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        # Update application
        application.cl_latex = cl_latex
        db.commit()

        return ClGenerationResponse(cl_latex=cl_latex)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate cover letter: {str(e)}")

@app.post("/applications/", response_model=JobApplicationResponse)
async def create_application(
    request: JobApplicationRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Create a new job application by extracting JD from URL and generating CV/cover letter LaTeX
    """
    try:
        # Extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, request.job_url)

        # Create output directory
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)

        # Save JD text (sanitize title for filesystem safety)
        import re as _re
        safe_title = _re.sub(r'[\\/:"*?<>|]+', '_', title)
        jd_txt_path = os.path.join(out_dir, f"{safe_title}.txt")
        os.makedirs(os.path.dirname(jd_txt_path), exist_ok=True)
        with open(jd_txt_path, "w", encoding="utf-8") as f:
            f.write(jd_text)

        # Generate LaTeX content (directly to database)
        cv_latex = compile_cv_tex(client, jd_text)
        cl_latex, _ = compile_cl_tex(client, jd_text, company, title, cv_latex)

        # Create application record
        application = Application(
            jb_url=request.job_url,
            jd_text=jd_text,
            company=company,
            title=title,
            cv_latex=cv_latex,
            cl_latex=cl_latex
        )

        # Save to database
        db.add(application)
        db.commit()
        db.refresh(application)

        return JobApplicationResponse(
            id=application.id,
            job_url=application.jb_url,
            company=application.company,
            title=application.title,
            jd_text=application.jd_text,
            cv_latex=application.cv_latex,
            cl_latex=application.cl_latex,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create application: {str(e)}")

@app.get("/applications/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_dependency)
):
    """
    List all applications with pagination
    """
    applications = db.query(Application).offset(skip).limit(limit).all()

    return ApplicationListResponse(
        applications=[
            JobApplicationResponse(
                id=app.id,
                job_url=app.jb_url,
                company=app.company,
                title=app.title,
                jd_text=app.jd_text,
                cv_latex=app.cv_latex,
                cl_latex=app.cl_latex,
                created_at=app.created_at,
                updated_at=app.updated_at
            )
            for app in applications
        ]
    )

@app.get("/applications/{application_id}", response_model=JobApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get a specific application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return JobApplicationResponse(
        id=application.id,
        job_url=application.jb_url,
        company=application.company,
        title=application.title,
        jd_text=application.jd_text,
        cv_latex=application.cv_latex,
        cl_latex=application.cl_latex,
        created_at=application.created_at,
        updated_at=application.updated_at
    )

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
                error_msg = f"PDF file was not generated. Return code: {proc.returncode}, stdout: {proc.stdout[:200]}, stderr: {proc.stderr[:200]}"
                raise HTTPException(status_code=500, detail=error_msg)

            # Stream the PDF file
            def file_stream_generator():
                try:
                    with open(pdf_path, "rb") as f:
                        while True:
                            chunk = f.read(64 * 1024)  # Read in 64KB chunks
                            if not chunk:
                                break
                            yield chunk
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error streaming PDF: {str(e)}")

            return StreamingResponse(
                file_stream_generator(),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compilation failed: {str(e)}")


def latex_to_html(latex_content: str) -> str:
    """
    Basic LaTeX to HTML converter for CV/Cover Letter
    This is a simplified converter - in production you'd want a more robust solution
    """
    # Basic HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .cv-paragraph {{ margin: 20px 0; }}
            .section {{ margin: 30px 0; }}
            h1, h2, h3 {{ color: #333; }}
            .contact {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """

    # Basic LaTeX to HTML conversion
    content = latex_content

    # Convert basic LaTeX commands to HTML
    content = content.replace('\\cvparagraph{', '<div class="cv-paragraph">')
    content = content.replace('}', '</div>')
    content = content.replace('\\section{', '<h2>')
    content = content.replace('\\subsection{', '<h3>')
    content = content.replace('\\textbf{', '<strong>')
    content = content.replace('\\textit{', '<em>')

    # Remove LaTeX-specific commands that don't convert well
    content = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', content)

    return html_template.format(content=content)


@app.delete("/applications/{application_id}")
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

    return {"message": "Application deleted successfully"}

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
