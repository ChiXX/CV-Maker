import os
import subprocess
import shutil
import tempfile
import re
from prompts import cv_profile_summary_prompt_template


def compile_cv_tex(client, out_dir, jd_text):
    source_dir = "./latex_cv"
    main_tex_file = "sample.tex"
    os.makedirs(out_dir, exist_ok=True)
    print("✍️ Updating CV")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 拷贝所有内容到临时目录
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(temp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # === 替换 summary ===
        modify_tex(client, temp_dir, main_tex_file, jd_text)

        # 编译主 tex 文件
        subprocess.run(
            ["pdflatex", "-interaction=batchmode", main_tex_file], cwd=temp_dir
        )

        # 拷贝输出 PDF
        # 🛠️ 创建输出目录（如果需要）
        generated_pdf = os.path.join(
            temp_dir, os.path.splitext(main_tex_file)[0] + ".pdf"
        )
        if os.path.exists(generated_pdf):
            shutil.copy(generated_pdf, os.path.join(out_dir, os.getenv("OUTPUT_CV")))
            print(f"✅ Compilation complete. CV saved to: {out_dir}")
        else:
            raise FileNotFoundError("❌ Failed to generate PDF")


def modify_tex(client, temp_dir, main_tex_file, jd_text):
    tex_path = os.path.join(temp_dir, main_tex_file)

    # === 读取 tex 内容 ===
    with open(tex_path, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === 提取当前 summary ===
    match = re.search(r"\\cvparagraph\{(.*?)\}", tex_text, flags=re.DOTALL)
    if not match:
        raise ValueError("❌ Could not find \\cvparagraph{...}")

    # === 构造 prompt 并调用 OpenRouter ===
    MAX_LENGTH = 220
    new_summary = ""
    prompt = cv_profile_summary_prompt_template.format(
        jd_text=jd_text, max_length=MAX_LENGTH
    )
    for _ in range(3):
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        candidate = response.choices[0].message.content.strip()

        plain_text = re.sub(r"\\strong\{(.*?)\}", r"\1", candidate)

        if len(plain_text) <= MAX_LENGTH + 30:
            new_summary = candidate
            break
        else:
            print(f"⚠️ Summary too long ({len(candidate)} chars), retrying...")

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

