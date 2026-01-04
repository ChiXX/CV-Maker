from typing import List, Dict, Any
import re

class Planner:
    """Shared Planner class for both CV and Cover Letter generation."""

    def __init__(self, client, prompt_template: str):
        self.client = client
        self.prompt_template = prompt_template

    def build_plan(self, jd_text: str, context_data) -> List[str]:
        """Build a comprehensive plan using the provided prompt template."""

        # Call LLM to generate the plan
        try:
            response = self.client.chat.completions.create(
                model="mistralai/devstral-2512:free",
                messages=[
                    {"role": "system", "content": "You are a planning expert. Generate structured plans in the exact format requested."},
                    {"role": "user", "content": self.prompt_template.format(jd_text=jd_text, context_data=context_data)}
                ],
                temperature=0.1,  # Lower temperature for more consistent planning
            )

            plan_response = response.choices[0].message.content.strip()

            # Parse the Python list from the response
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
    """Shared Solver class for both CV and Cover Letter generation."""

    def __init__(self, client, prompt_template: str, resume_data):
        self.client = client
        self.prompt_template = prompt_template
        self.resume_data = resume_data

    def execute(self, plan: List[str], jd_text: str, **kwargs) -> str:
        """Execute the comprehensive plan."""

        history = ""
        for i, step in enumerate(plan):
            solver_prompt = self.prompt_template.format(
                plan=plan,
                resume_data=self.resume_data,
                jd_text=jd_text,
                history=history,
                step=step,
                **kwargs
            )
            response = self.client.chat.completions.create(
                model="mistralai/devstral-2512:free",
                messages=[
                    {"role": "user", "content": solver_prompt},
                ],
                temperature=0.1,
            )
            response_text = response.choices[0].message.content.strip()
            history += f"step {i+1}: {step}\nresult: {response_text}\n\n"

        return response_text
