import re
from app.services.planner_and_solver import Planner, Solver
from app.core.prompts import CV_PLANNER_PROMPT, CV_SOLVER_PROMPT
from app.services.shared_resume import resume_data


from app.utils.latex import escape_latex

def get_cv_template():
    main_tex_file = "./latex_cv/sample.tex"
    print("✍️ Generating CV LaTeX")

    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_template = f.read()
    return tex_template

def wrap_cv_in_latex(summary: str) -> str:
    tex_template = get_cv_template()
    escaped_summary = escape_latex(summary)
    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{escaped_summary}{m.group(3)}",
        tex_template,
        flags=re.DOTALL,
    )
    return tex_text_updated


def compile_cv_tex(client, jd_text):
    print("✍️ Generating CV Content")

    # === Plan and solve for CV summary generation ===
    planner = Planner(client, CV_PLANNER_PROMPT, jd_text)
    solver = Solver(client, CV_SOLVER_PROMPT, jd_text, resume_data)

    plan = planner.build_plan()
    new_summary = solver.execute(plan, mode="cv")

    print(f"✅ CV Content Generated")

    return new_summary, plan
