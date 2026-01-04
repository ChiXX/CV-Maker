import os
import re
from typing import List, Dict, Any
from shared_planner import Planner, Solver
from shared_prompts import CL_PLANNER_PROMPT, CL_SOLVER_PROMPT
from shared_resume import resume_data







def compile_cl_tex(client, jd_text, company, title, cv_latex, interactive=False):
    main_tex_file = "./latex_cl/sample.tex"
    print("✍️ Generating CL LaTeX")

    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # Plan and solve for cover letter generation
    # planner = Planner(client, CL_PLANNER_PROMPT)
    # solver = Solver(client, CL_SOLVER_PROMPT, cv_latex)

    # plan = planner.build_plan(jd_text, cv_latex)
    # letter_body = solver.execute(plan, jd_text, company=company, title=title, cv_latex=cv_latex)
    plan = ["test","test2"]
    letter_body = "test"
    # Format for LaTeX
    formatted_paragraphs = [
        line.strip() for line in letter_body.split("\n") if line.strip()
    ]
    formatted_letter = "\n\n\\vspace{0.5cm}\n\n".join(formatted_paragraphs)
    new_tex = tex_text.replace("% Inject here", formatted_letter)

    # Print a short preview for logs
    preview = letter_body if len(letter_body) < 500 else letter_body[:500] + "..."
    print(f"✅ CL LaTeX generated (preview): {preview}")
    # Return new tex, the letter body, and the plan steps for frontend display
    return new_tex, letter_body, plan


