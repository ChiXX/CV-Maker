import os
import subprocess
import shutil
import tempfile
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# ==== 加载环境变量 ====
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)


def extract_jd_from_url_with_llm(url):
    try:
        print(f"🌐 Fetching job page content: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        raw_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        visible_text = "\n".join(lines[:200])  # 限制长度

        prompt = f"""
You are a helpful assistant. You will be given the visible HTML text from a job listing.

You will be given a raw HTML job listing content and its URL. Your task is to extract:
1. The full Job Description text.
2. The company name.
3. The job title.
If the content is not in English, translate it into English
Output them in this format:

### JD:
(full job description)

### Company:
(company name)

### Title:
(job title)

Only extract what's visible from the content or logically inferrable from the URL. If you cannot identify the content from the webpage, respond with:

### JD:
[FAILED]

### Company:
[UNKNOWN]

### Title:
[UNKNOWN]

---
Source URL: {url}

{visible_text}
"""
        print("🤖 Calling model to extract JD information")
        response = client.chat.completions.create(
            model="mistralai/mistral-small-3.1-24b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content

        jd, company, title = "", "Company", "Job"
        match_jd = re.search(r"### JD:\n(.*?)\n### Company:", content, re.DOTALL)
        match_co = re.search(r"### Company:\n(.*?)\n### Title:", content, re.DOTALL)
        match_tt = re.search(r"### Title:\n(.*)$", content, re.DOTALL)
        if match_jd:
            jd = match_jd.group(1).strip()
        if match_co:
            company = match_co.group(1).strip()
        if match_tt:
            title = match_tt.group(1).strip()

        if jd == "[FAILED]":
            print("❌ Failed to fetch job page")
            jd = input("❗Could not access URL. Please paste the job description manually:\n")
            company = input("Enter company name: ") or "Company"
            title = input("Enter job title: ") or "Job"
            return jd, company, title

        print(f"✅ Extraction completed → Company: {company}, Title: {title}")
        return jd, company, title

    except Exception as e:
        print(f"❌ Failed to fetch job page: {e}")
        jd = input("❗Could not access URL. Please paste the job description manually:\n")
        company = input("Enter company name: ") or "Company"
        title = input("Enter job title: ") or "Job"
        return jd, company, title


def modify_tex(temp_dir, main_tex_file, jd_text):
    tex_path = os.path.join(temp_dir, main_tex_file)

    # === 读取 tex 内容 ===
    with open(tex_path, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === 提取当前 summary ===
    match = re.search(r"\\cvparagraph\{(.*?)\}", tex_text, flags=re.DOTALL)
    if not match:
        raise ValueError("❌ Could not find \\cvparagraph{...}")
    current_summary = match.group(1).strip()

    # === 构造 prompt 并调用 OpenRouter ===
    prompt = f"""
You are a resume rewriting agent. Your task is to rewrite the candidate's profile summary
so that it best matches the job description below — but only by rephrasing or reordering what
already exists in the resume. Do NOT invent or exaggerate skills, tools, or responsibilities.

# Job Description
{jd_text}

# Current Profile Summary
{current_summary}

# Other Resume Content
The candidate is a full stack developer with 3 years of experience in:
- Python, Flask, RESTful APIs, PostgreSQL
- Frontend: React, HTMX, Bootstrap, Jinja2
- DevOps: Docker, GitLab CI/CD, AWS
- Scientific projects involving bioinformatics and antibody/protein data
- Testing: Jest, Cypress, Pytest
- Degree in Bioinformatics (MSc) and Biomedical Engineering (BSc)

# Output Instructions
- Rewrite the profile summary to better match the job description.
- The result must be under 300 characters (not words).
- Highlight key skills, tools, and areas of strength using LaTeX format: wrap them in \\strong{{...}}.
- Do not fabricate or exaggerate. Only use what is already in the resume.
- Do not include quotation marks or markdown.
"""

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    new_summary = response.choices[0].message.content.strip()

    # === 替换 LaTeX 内容 ===
    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{new_summary}{m.group(3)}",
        tex_text,
        flags=re.DOTALL,
    )

    # === 写回临时目录 ===
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_text_updated)

    print("✍️ Summary updated in LaTeX file")


def compile_tex_project(source_dir, main_tex_file, out_dir, jd_text):
    os.makedirs(out_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Copying LaTeX project into temporary directory: {temp_dir}")
        # 拷贝所有内容到临时目录
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(temp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # === 替换 summary ===
        modify_tex(temp_dir, main_tex_file, jd_text)

        # 编译主 tex 文件
        subprocess.run(
            ["pdflatex", "-interaction=batchmode", main_tex_file], cwd=temp_dir
        )

        # 拷贝输出 PDF
        # 🛠️ 创建输出目录（如果需要）
        generated_pdf = os.path.join(temp_dir, os.path.splitext(main_tex_file)[0] + ".pdf")
        if os.path.exists(generated_pdf):
            shutil.copy(generated_pdf, os.path.join(out_dir, os.getenv("OUTPUT_CV")))
            print(f"✅ Compilation complete. PDF saved to: {out_dir}")
        else:
            raise FileNotFoundError("❌ PDF 未生成")


if __name__ == "__main__":
    url = input("🔗 请输入职位链接: ").strip()
    jd_text, company, title = extract_jd_from_url_with_llm(url)
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join("Applications", f"{company}-{today}")

    os.makedirs(out_dir, exist_ok=True)
    jd_txt_path = os.path.join(out_dir, f"{title}.txt")
    with open(jd_txt_path, "w", encoding="utf-8") as f:
        f.write(jd_text)

    SOURCE_DIR = "./latex"
    MAIN_TEX_FILE = "sample.tex"

    compile_tex_project(SOURCE_DIR, MAIN_TEX_FILE, out_dir, jd_text)
