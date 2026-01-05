from typing import List, Dict, Any
import ast
import re
from datetime import datetime

class Planner:
    """Shared Planner class for both CV and Cover Letter generation."""

    def __init__(self, client, prompt_template: str, jd_text: str):
        self.client = client
        self.prompt_template = prompt_template
        self.jd_text = jd_text

    def build_plan(self) -> List[str]:
        """Build a comprehensive plan using the provided prompt template."""
        
        current_date = datetime.now().strftime("%Y-%m-%d")

        response = self.client.chat.completions.create(
            model="mistralai/devstral-2512:free",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional Career Auditor and Planning Expert. Output ONLY a Python list."
                },
                {
                    "role": "user", 
                    "content": self.prompt_template.format(
                        jd_text=self.jd_text, 
                        current_date=current_date,
                    )
                }
            ],
            temperature=0.1,  # Low temperature is vital for structural consistency
        )
        
        content = response.choices[0].message.content.strip()
        try:
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if not match:
                raise ValueError("No list found")
            
            plans = ast.literal_eval(match.group(0))
            print( "plans: ", plans)
            return plans

        except Exception as e:
            raise Exception(f"Failed to build plan: {str(e)}")


class Solver:
    """Shared Solver class for both CV and Cover Letter generation."""

    def __init__(self, client, prompt_template: str, jd_text: str, resume_data):
        self.client = client
        self.prompt_template = prompt_template
        self.jd_text = jd_text
        self.resume_data = resume_data

    def execute(self, plan: List[str]) -> str:
        """Execute the comprehensive plan."""
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        history = ""
        last_final_answer = ""
        
        try:
            for i, step in enumerate(plan):
                prompt = self.prompt_template.format(
                    plan=plan, 
                    step=step.split(":")[-1] + "Max 150 chars" if i == len(plan) - 1 else "", 
                    history=history, 
                    jd_text=self.jd_text, 
                    resume_data=self.resume_data, 
                    current_date=current_date
                )

                response = self.client.chat.completions.create(
                    model="mistralai/devstral-2512:free",
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                )
                content = response.choices[0].message.content.strip()
                answer_match = re.search(r'<answer>(.*?)</answer>', content, re.DOTALL)
                if answer_match:
                    step_result = answer_match.group(1).strip()
                else:
                    step_result = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
                
                step_result = step_result.strip(' "\'*-•')
                print('*'*10)
                print(step)
                print('-'*10)
                print(step_result)
                print('*'*10)
                if i == len(plan) - 1:
                    # Final headline polish
                    last_final_answer = step_result.split('\n')[0] 
                else:
                    last_final_answer = step_result

                history += f"Step {i+1} Result: {last_final_answer}\n\n"
                
            return last_final_answer
        except Exception as e:
            raise Exception(f"Failed to execute solver at step {i+1}: {str(e)}, history: {history}")
