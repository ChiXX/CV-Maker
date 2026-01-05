import re
from planner_and_solver import Planner, Solver
from shared_prompts import CV_PLANNER_PROMPT, CV_SOLVER_PROMPT
from shared_resume import resume_data


def compile_cv_tex(client, jd_text):
    main_tex_file = "./latex_cv/sample.tex"
    print("✍️ Generating CV LaTeX")

    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === Plan and solve for CV summary generation ===
    planner = Planner(client, CV_PLANNER_PROMPT, jd_text)
    solver = Solver(client, CV_SOLVER_PROMPT, jd_text, resume_data)

    plan = planner.build_plan()
    new_summary = solver.execute(plan, mode="cv")

    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{new_summary}{m.group(3)}",
        tex_text,
        flags=re.DOTALL,
    )

    print(f"✅ CV LaTeX: {new_summary}")

    return tex_text_updated, new_summary, plan
