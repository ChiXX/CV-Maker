import os
import subprocess
import shutil
import tempfile
from prompts import cover_letter_prompt_template


def compile_cl_tex(client, out_dir, jd_text, company, title):
    source_dir = "./latex_cl"
    main_tex_file = "sample.tex"
    os.makedirs(out_dir, exist_ok=True)
    print("✍️ Writing CL")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 拷贝所有内容到临时目录
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(temp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        letter = write_cover_letter(
            client, temp_dir, main_tex_file, jd_text, company, title
        )
        letter_txt_path = os.path.join(out_dir, "cover_letter.txt")
        with open(letter_txt_path, "w", encoding="utf-8") as f:
            f.write(letter)

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
            shutil.copy(generated_pdf, os.path.join(out_dir, os.getenv("OUTPUT_CL")))
            print(f"✅ Compilation complete. CL saved to: {out_dir}")
        else:
            raise FileNotFoundError("❌ Failed to generate PDF")


def write_cover_letter(client, temp_dir, main_tex_file, jd_text, company, title):
    tex_path = os.path.join(temp_dir, main_tex_file)

    with open(tex_path, "r", encoding="utf-8") as f:
        tex_text = f.read()

    prompt = cover_letter_prompt_template.format(
        jd_text=jd_text,
        company=company,
        title=title,
        name=os.getenv("NAME")
    )

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    letter_body = response.choices[0].message.content.strip()

    formatted_paragraphs = [
        line.strip() for line in letter_body.split("\n") if line.strip()
    ]
    formatted_letter = "\n\n\\vspace{0.5cm}\n\n".join(formatted_paragraphs)

    # Inject into tex content
    new_tex = tex_text.replace("% Inject here", formatted_letter)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(new_tex)

    return letter_body
