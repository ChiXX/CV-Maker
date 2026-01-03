import os
import re
from typing import List, Dict, Any


class Planner:
    
    def __init__(self, client):
        self.client = client
        self.planner_prompt = """
        You are an AI planner for CV head line generation. Break down the task into executable steps.
        The generated head line should be a short sentence no more than 150 characters and can be used as a CV head line.
        Do not mock or exaggerate the resume inventory. Especially the experience, skills, and work experience should be accurate and concise.

        Job Description: {jd_text}
        Resume Inventory: {resume_inventory}

        Output a Python list of steps:
        ```python
        [
            step_1,
            step_2,
            step_3,
            ....,
        ]
        ```
        """
    
    def build_plan(self, jd_text: str, resume_inventory: Dict[str, Any]) -> List[str]:
        """Build a comprehensive plan for generating a validated CV summary using Plan-and-Solve pattern.
        """
        

        # Call LLM to generate the plan
        try:
            response = self.client.chat.completions.create(
                model="mistralai/devstral-2512:free",
                messages=[
                    {"role": "system", "content": "You are a planning expert. Generate structured plans in the exact format requested."},
                    {"role": "user", "content": self.planner_prompt.format(jd_text=jd_text, resume_inventory=resume_inventory )}
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
        self.resume_skills = {
            'languages': ['Python', 'Node.js', 'JavaScript'],
            'frameworks': ['Flask', 'SQLAlchemy', 'Lit.js', 'D3.js'],
            'databases': ['PostgreSQL', 'MongoDB'],
            'tools': ['Docker', 'GitLab CI/CD', 'AWS EC2', 'Playwright', 'Jinja2'],
            'domains': ['Full Stack Development', 'Bioinformatics', 'Biomedical Engineering'],
            'experience': {
                'SAGA Diagnostics': '2023.11–present (~2 year)',
                'Bionamic': '2022.3–2023.10 (~1.6 years)',
                'total_years': '~3.6 years'
            }
        }
        self.solver_prompt = """
        You are a solver for CV head line generation. 
        You will strictly follow the plan and solve the problem step by step.
        You ill be given a plan, a resume inventory, a job description, and a history.
        You will focus on the current step and output the answer for the current step. 
        Do not output anything not related to the current step and explain your thinking process.
        
        
        # Plan: {plan}
        
        # Resume Inventory: {resume_skills}
        
        # Job Description: {jd_text}
        
        # history: {history}
        
        # Current Step: {step}
        
        Onnly output the answer for the current step.

        """
        
        

    def execute(self, plan: List[str], jd_text) -> str:
        """Execute the comprehensive plan to generate and verify a CV summary using Plan-and-Solve.
        """
        history = ""
        
        for i,step in enumerate(plan):
            solver_prompt = self.solver_prompt.format(plan=plan, resume_skills=str(self.resume_skills), jd_text=jd_text, history=history, step=step)
            response = self.client.chat.completions.create(
                model="mistralai/devstral-2512:free",
                messages=[
                    {"role": "user", "content": solver_prompt},
                ],
                temperature=0.1,
            )
            response_text = response.choices[0].message.content.strip()
            history += f"step {i+1}: {step}\nresult: {response_text}"
            print(step, response_text)

        return response_text
        


def compile_cv_tex(client, jd_text):
    main_tex_file = "./latex_cv/sample.tex"
    print("✍️ Generating CV LaTeX")

    # Read the LaTeX template directly
    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === Plan and solve for CV summary generation ===
    planner = Planner(client)
    solver = Solver(client)
    
    plan = planner.build_plan(jd_text, solver.resume_skills)
    new_summary = solver.execute(plan, jd_text)

    # === 替换 LaTeX 内容 ===
    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{new_summary}{m.group(3)}",
        tex_text,
        flags=re.DOTALL,
    )

    print(f"✅ CV LaTeX: {new_summary}")
    return tex_text_updated, new_summary


