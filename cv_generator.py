import os
import re
from typing import List, Dict, Any
from shared_planner import Planner, Solver
from shared_prompts import CV_PLANNER_PROMPT, CV_SOLVER_PROMPT
from shared_resume import resume_data
        


def compile_cv_tex(client, jd_text):
    main_tex_file = "./latex_cv/sample.tex"
    print("✍️ Generating CV LaTeX")

    # Read the LaTeX template directly
    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === Plan and solve for CV summary generation ===
    # planner = Planner(client, CV_PLANNER_PROMPT)
    # solver = Solver(client, CV_SOLVER_PROMPT, resume_data)

    # plan = planner.build_plan(jd_text, resume_data)
    # execute returns the final result text after running solver through steps
    # new_summary = solver.execute(plan, jd_text)
    new_summary = "test"
    plan = ["test","test2"]

    # === 替换 LaTeX 内容 ===
    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{new_summary}{m.group(3)}",
        tex_text,
        flags=re.DOTALL,
    )

    print(f"✅ CV LaTeX: {new_summary}")
    # Return the updated tex, the new summary, and the plan steps for frontend display
    return tex_text_updated, new_summary, plan


