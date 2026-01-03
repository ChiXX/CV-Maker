import os
import re
from prompts import cv_profile_summary_prompt_template


def compile_cv_tex(client, jd_text):
    main_tex_file = "./latex_cv/sample.tex"
    print("✍️ Generating CV LaTeX")

    # Read the LaTeX template directly
    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # === 提取当前 summary ===
    match = re.search(r"\\cvparagraph\{(.*?)\}", tex_text, flags=re.DOTALL)
    if not match:
        raise ValueError("❌ Could not find \\cvparagraph{...}")

    # === 构造 prompt 并调用 OpenRouter ===
    new_summary = interactive_summary_review(client, jd_text)

    # === 替换 LaTeX 内容 ===
    tex_text_updated = re.sub(
        r"(\\cvparagraph\{)(.*?)(\})",
        lambda m: f"{m.group(1)}{new_summary}{m.group(3)}",
        tex_text,
        flags=re.DOTALL,
    )

    print("✅ CV LaTeX generated successfully")
    return tex_text_updated


def interactive_summary_review(client, jd_text, max_length=220):
    # Resume content for verification (source of truth)
    resume_skills = {
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

    def verify_summary(summary_text, max_length):
        """Verify that summary contains only valid skills and experience, and meets length requirements"""
        issues = []

        # Extract plain text for all validations
        plain_text = re.sub(r"\\strong\{(.*?)\}", r"\1", summary_text)

        # Check length constraint
        if len(plain_text) > max_length + 30:
            issues.append(f"Length exceeds limit: {len(plain_text)} chars (max: {max_length + 30})")

        # Check for mock/fake skills
        words = re.findall(r'\b\w+\b', plain_text.lower())

        # Define known valid terms
        valid_terms = set()
        for category in resume_skills.values():
            if isinstance(category, dict):
                for value in category.values():
                    if isinstance(value, str):
                        valid_terms.update(re.findall(r'\b\w+\b', value.lower()))
            elif isinstance(category, list):
                for item in category:
                    valid_terms.update(re.findall(r'\b\w+\b', item.lower()))

        # Add common tech terms that are valid
        valid_terms.update(['full', 'stack', 'developer', 'web', 'api', 'data', 'development'])

        # Check for potentially fake skills
        suspicious_terms = []
        for word in words:
            if len(word) > 3 and word not in valid_terms and not any(word in item.lower() for item in resume_skills['languages'] + resume_skills['frameworks'] + resume_skills['tools']):
                suspicious_terms.append(word)

        if suspicious_terms:
            issues.append(f"Potentially mock skills detected: {', '.join(suspicious_terms[:3])}")

        # Check for incorrect working years
        if 'years' in plain_text.lower() or any(char.isdigit() for char in plain_text):
            # Look for year patterns
            year_patterns = re.findall(r'\b\d+(?:\.\d+)?\s*(?:years?|yrs?)\b', plain_text.lower())
            for pattern in year_patterns:
                if '3' in pattern or '4' in pattern or '5' in pattern:
                    issues.append(f"Incorrect working years detected: {pattern} (actual: ~2.6 years)")

        return issues

    def create_verification_prompt(candidate_summary, issues):
        """Create a prompt for the verification agent"""
        return f"""
You are a verification agent. Review this candidate summary for a resume profile:

CANDIDATE SUMMARY: {candidate_summary}

VERIFICATION ISSUES FOUND: {', '.join(issues) if issues else 'None'}

RESUME CONSTRAINTS:
- Skills: {', '.join(resume_skills['languages'] + resume_skills['frameworks'] + resume_skills['databases'] + resume_skills['tools'])}
- Experience: {resume_skills['experience']['total_years']} total
- Must not contain mock/fake skills or incorrect working years

Task: If issues are found, provide specific correction instructions. If no issues, respond with "VERIFIED".

Response format:
VERIFICATION: [VERIFIED/ISSUES_FOUND]
DETAILS: [specific feedback or confirmation]
"""

    # Initial prompt for summary generation
    messages = [
        {
            "role": "system",
            "content": "You are a resume optimization agent using ReAct pattern. Generate summaries that match job descriptions using only real resume content. Never fabricate skills or exaggerate experience.",
        },
        {
            "role": "user",
            "content": cv_profile_summary_prompt_template.format(
                jd_text=jd_text,
                max_length=max_length,
            ),
        },
    ]

    verification_history = []
    max_verification_attempts = 3
    candidate = ""  # Initialize to avoid NameError if all attempts fail

    for attempt in range(max_verification_attempts):
        print(f"\n🔄 Verification Loop {attempt + 1}/{max_verification_attempts}")

        # Step 1: Generate candidate summary
        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=messages,
            )
            candidate = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Generation error: {e}")
            continue

        # Step 2: Verify the candidate (includes length, skills, and experience checks)
        issues = verify_summary(candidate, max_length)
        verification_history.append({
            'attempt': attempt + 1,
            'candidate': candidate,
            'issues': issues,
            'verified': len(issues) == 0
        })

        print(f"📄 Candidate Summary: {candidate}")
        print(f"📏 Length: {len(candidate)} chars (max: {max_length})")
        print(f"🔍 Issues Found: {len(issues)}")

        if issues:
            print(f"⚠️  Issues: {', '.join(issues)}")
        else:
            print("✅ Verification Passed!")

        # Step 3: If verified, return the result
        if len(issues) == 0:
            print("🎉 Summary verified and accepted!")
            return candidate

        # Step 4: If not verified, get verification feedback and regenerate
        if attempt < max_verification_attempts - 1:
            # Create verification prompt
            verification_prompt = create_verification_prompt(candidate, issues)

            # Get verification feedback
            verification_messages = [
                {"role": "system", "content": "You are a verification agent. Analyze summaries for accuracy against resume content."},
                {"role": "user", "content": verification_prompt}
            ]

            try:
                verification_response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL"),
                    messages=verification_messages,
                )
                feedback = verification_response.choices[0].message.content.strip()

                # Add feedback to conversation history
                messages.append({"role": "assistant", "content": candidate})
                messages.append({"role": "user", "content": f"VERIFICATION FAILED: {', '.join(issues)}\n\nFEEDBACK: {feedback}\n\nPlease regenerate with corrections."})

                print(f"🔧 Feedback received, regenerating...")
            except Exception as e:
                print(f"❌ Verification error: {e}")
                continue

    # If all attempts failed, return the last candidate with warning or raise error if no candidate was generated
    print("⚠️  Maximum verification attempts reached. Returning last candidate.")
    if not candidate:
        raise Exception("Failed to generate CV summary after maximum attempts. Please check OpenAI API configuration and try again.")

    return candidate
