import os
from openai import OpenAI

from datetime import datetime
from dotenv import load_dotenv
from cv_generator import compile_cv_tex
from cl_generator import compile_cl_tex
from jd_generator import extract_jd_from_url_with_llm


# ==== 加载环境变量 ====
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)


if __name__ == "__main__":
    url = input("🔗 Please paste the job link: ").strip()
    jd_text, company, title = extract_jd_from_url_with_llm(client, url)
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join("Applications", f"{company}-{today}")

    os.makedirs(out_dir, exist_ok=True)
    jd_txt_path = os.path.join(out_dir, f"{title}.txt")
    with open(jd_txt_path, "w", encoding="utf-8") as f:
        f.write(jd_text)

    compile_cv_tex(client, out_dir, jd_text)
    compile_cl_tex(client, out_dir, jd_text, company, title)
