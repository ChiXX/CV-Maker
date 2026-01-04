import os
import re
from typing import List, Dict, Any
from prompts import cover_letter_prompt_template
import sys

# Resume content for verification (source of truth)
resume_skills = {
    'languages': ['Python', 'Node.js', 'JavaScript', 'TypeScript', 'C/C++'],
    'frameworks': ['Flask', 'SQLAlchemy', 'Lit.js', 'D3.js', 'React', 'Next.js', 'jQuery', 'Bootstrap'],
    'databases': ['PostgreSQL', 'MongoDB'],
    'tools': ['Docker', 'GitLab CI/CD', 'GitHub Actions', 'AWS', 'Playwright', 'Jinja2'],
    'domains': ['Full Stack Development', 'Bioinformatics', 'Biomedical Engineering', 'Machine Learning'],
    'experience': {
        'SAGA Diagnostics': 'Nov 2023 - Present (~1 year)',
        'Bionamic': 'Mar 2022 - Oct 2023 (~1.6 years)',
        'total_years': '~2.6 years'
    }
}


class Planner:

    def __init__(self, client):
        self.client = client
        self.planner_prompt = """
        You are an AI planner for cover letter generation. Break down the task into executable steps. But the steps should with in 6 steps.
        The generated cover letter should be authentic, align with job requirements, and contain only verified skills and experience from the provided CV LaTeX.
        Do not mock or exaggerate the resume content. Especially the experience, skills, and work experience should be accurate and concise.
        Generate the pure letter body in the final step.

        Job Description: {jd_text}
        CV LaTeX (contains resume information): {cv_latex}

        Output a Python list of steps:
        ```python
        [
            step_1,
            step_2,
            step_3,
            ....,
        ]
        """

    def build_plan(self, jd_text: str, cv_latex: str) -> List[str]:
        """Build a comprehensive plan for generating a validated cover letter using Plan-and-Solve pattern."""

        # Call LLM to generate the plan
        try:
            response = self.client.chat.completions.create(
                model="mistralai/devstral-2512:free",
                messages=[
                    {"role": "system", "content": "You are a planning expert. Generate structured plans in the exact format requested."},
                    {"role": "user", "content": self.planner_prompt.format(jd_text=jd_text, cv_latex=cv_latex )}
                ],
                temperature=0.1,  # Lower temperature for more consistent planning
            )

            plan_response = response.choices[0].message.content.strip()

            # Parse the Python list from the response
            import re
            python_code_match = re.search(r'```python\s*\n(.*?)\n```', plan_response, re.DOTALL)
            if not python_code_match:
                raise ValueError("Failed to parse plan from LLM response")

            # Safely evaluate the Python list
            plan_steps_text = python_code_match.group(1).strip()
            try:
                plan_steps = eval(plan_steps_text)
                if not isinstance(plan_steps, list):
                    raise ValueError("Plan is not a list")
            except:
                raise ValueError("Failed to parse plan steps as Python list")

            return plan_steps
        except Exception as e:
            raise Exception(f"Failed to build plan: {e}")


class Solver:
    def __init__(self, client):
        self.client = client
        self.resume_skills = resume_skills
        self.solver_prompt = """
        You are a solver for cover letter generation.
        You will strictly follow the plan and solve the problem step by step.
        You will be given a plan, CV LaTeX content (containing resume information), a job description, and a history.
        You will focus on the current step and output the answer for the current step.
        Do not output anything not related to the current step and explain your thinking process.


        # Plan: {plan}

        # CV LaTeX (resume information): {resume_skills}

        # Job Description: {jd_text}

        # history: {history}

        # Current Step: {step}

        Only output the answer for the current step.

        """

    def execute(self, plan: List[str], jd_text: str, company: str, title: str, cv_latex: str, interactive: bool = False) -> str:
        """Execute the comprehensive plan to generate and verify a cover letter using Plan-and-Solve."""

        # Execute the original plan
        history = ""
        for i, step in enumerate(plan):
            solver_prompt = self.solver_prompt.format(plan=plan, resume_skills=cv_latex, jd_text=jd_text, history=history, step=step)
            response = self.client.chat.completions.create(
                model="mistralai/devstral-2512:free",
                messages=[
                    {"role": "user", "content": solver_prompt},
                ],
                temperature=0.1,
            )
            response_text = response.choices[0].message.content.strip()
            history += f"step {i+1}: {step}\nresult: {response_text}"

        letter_body = response_text

        return letter_body





def compile_cl_tex(client, jd_text, company, title, cv_latex, interactive=False):
    main_tex_file = "./latex_cl/sample.tex"
    print("✍️ Generating CL LaTeX")

    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()
    
    # letter_body, formatted_letter = plan_and_solve_cover_letter(client, jd_text, company, title, cv_latex, interactive=interactive)
    planner = Planner(client)
    solver = Solver(client)

    plan = planner.build_plan(jd_text, cv_latex)
    letter_body = solver.execute(plan, jd_text, company, title, cv_latex, interactive=interactive)
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


