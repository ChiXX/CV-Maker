import os
from openai import OpenAI

from datetime import datetime
from dotenv import load_dotenv
from cv_generator import compile_cv_tex
from cl_generator import compile_cl_tex
from jd_generator import extract_jd_from_url_with_llm
from database import init_db, get_db
from models import Application


# ==== 加载环境变量 ====
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)


if __name__ == "__main__":
    # Initialize database
    init_db()

    url = input("🔗 Please paste the job link: ").strip()
    jd_text, company, title = extract_jd_from_url_with_llm(client, url)
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join("Applications", f"{today}-{company}")

    os.makedirs(out_dir, exist_ok=True)
    jd_txt_path = os.path.join(out_dir, f"{title}.txt")
    os.makedirs(os.path.dirname(jd_txt_path), exist_ok=True)
    with open(jd_txt_path, "w", encoding="utf-8") as f:
        f.write(jd_text)

    # Generate PDFs
    compile_cv_tex(client, out_dir, jd_text)
    compile_cl_tex(client, out_dir, jd_text, company, title)

    # Read PDF files and save to database
    db = get_db()

    # Read CV PDF
    cv_pdf_path = os.path.join(out_dir, os.getenv("OUTPUT_CV"))
    cv_pdf_data = None
    if os.path.exists(cv_pdf_path):
        with open(cv_pdf_path, "rb") as f:
            cv_pdf_data = f.read()

    # Read Cover Letter PDF
    cl_pdf_path = os.path.join(out_dir, os.getenv("OUTPUT_CL"))
    cl_pdf_data = None
    if os.path.exists(cl_pdf_path):
        with open(cl_pdf_path, "rb") as f:
            cl_pdf_data = f.read()

    # Create application record
    application = Application(
        jb_url=url,
        jd_text=jd_text,
        company=company,
        title=title,
        cv_pdf=cv_pdf_data,
        cl_pdf=cl_pdf_data
    )

    # Save to database
    db.add(application)
    db.commit()
    db.refresh(application)

    print(f"✅ Application saved to database with ID: {application.id}")

    db.close()
