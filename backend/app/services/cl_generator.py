import os
import re
from typing import List, Dict, Any
from app.services.planner_and_solver import Planner, Solver
from app.core.prompts import CL_PLANNER_PROMPT, CL_SOLVER_PROMPT
from app.services.shared_resume import resume_data

def compile_cl_tex(client, jd_text, company, title, cv_latex, interactive=False):
    main_tex_file = "./latex_cl/sample.tex"
    print("✍️ Generating CL LaTeX")

    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === Plan and solve for cover letter generation ===
    planner = Planner(client, CL_PLANNER_PROMPT, jd_text)
    solver = Solver(client, CL_SOLVER_PROMPT, jd_text, cv_latex)

    plan = planner.build_plan()
    letter_body = solver.execute(plan, mode='cl')
    # Format for LaTeX
    formatted_paragraphs = [
        line.strip() for line in letter_body.split("\n") if line.strip()
    ]
    formatted_letter = "\n\n\\vspace{0.5cm}\n\n".join(formatted_paragraphs)
    new_tex = tex_text.replace("% Inject here", formatted_letter)

    print(f"✅ CL LaTeX generated")

    return new_tex, letter_body, plan


