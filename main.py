from openai import OpenAI

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

    # Generate LaTeX content (no file operations)
    cv_latex = compile_cv_tex(client, jd_text)
    cl_latex = compile_cl_tex(client, jd_text, company, title)

    # Create application record with LaTeX content
    db = get_db()
    application = Application(
        jb_url=url,
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

    print(f"✅ Application saved to database with ID: {application.id}")
    print(f"   📄 CV LaTeX: {len(cv_latex)} characters")
    print(f"   📄 CL LaTeX: {len(cl_latex)} characters")

    db.close()
