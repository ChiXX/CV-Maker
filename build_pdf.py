import os
import subprocess
import shutil
import argparse
import tempfile
import re
from openai import OpenAI
from dotenv import load_dotenv

# ==== 加载环境变量 ====
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def modify_tex(temp_dir, main_tex_file, jd_path="jd.txt"):
    tex_path = os.path.join(temp_dir, main_tex_file)

    # === 读取 tex 内容 ===
    with open(tex_path, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === 提取当前 summary ===
    match = re.search(r"\\cvparagraph\{(.*?)\}", tex_text, flags=re.DOTALL)
    if not match:
        raise ValueError("❌ 没有找到 \\cvparagraph{...} 段落！")
    current_summary = match.group(1).strip()

    # === 读取 JD 内容 ===
    if not os.path.exists(jd_path):
        raise FileNotFoundError(f"❌ JD 文件 {jd_path} 不存在")
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read().strip()

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
            {"role": "user", "content": prompt}
        ]
    )
    new_summary = response.choices[0].message.content.strip()

    # === 替换 LaTeX 内容 ===
    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{new_summary}{m.group(3)}",
        tex_text,
        flags=re.DOTALL
    )

    # === 写回临时目录 ===
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_text_updated)

    print(f"✍️ 已更新 LaTeX 文件中的 summary: \n {new_summary}")


def run_cmd(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    # print(result.stdout)
    if result.returncode != 0:
        # print(f"⚠️ 命令有警告（返回码 {result.returncode}）：{' '.join(cmd)}")
        print(result.stderr)

def compile_tex_project(source_dir, main_tex_file, output_pdf_path):
    pdf_name = os.path.splitext(main_tex_file)[0] + ".pdf"

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 正在复制项目到临时目录: {temp_dir}")
        # 拷贝所有内容到临时目录
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(temp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        
        # === 替换 summary ===
        modify_tex(temp_dir, main_tex_file)
        

        # 编译主 tex 文件
        run_cmd(["pdflatex", "-interaction=batchmode", main_tex_file], cwd=temp_dir)

        # 拷贝输出 PDF
        # 🛠️ 创建输出目录（如果需要）
        os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)
        generated_pdf = os.path.join(temp_dir, pdf_name)
        if os.path.exists(generated_pdf):
            shutil.copy(generated_pdf, output_pdf_path)
            print(f"✅ 编译完成，PDF 已保存至: {output_pdf_path}")
        else:
            raise FileNotFoundError("❌ PDF 未生成")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="安全编译 LaTeX 项目并输出 PDF")
    parser.add_argument("--out", help="输出 PDF 文件路径", default="output.pdf")
    args = parser.parse_args()

    SOURCE_DIR = "./latex"
    MAIN_TEX_FILE = "sample.tex"

    compile_tex_project(SOURCE_DIR, MAIN_TEX_FILE, args.out)
