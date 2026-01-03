import os
import re
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


def verify_cover_letter(letter_text):
    """Verify that cover letter contains only valid skills and experience"""
    issues = []

    # Check for mock/fake skills
    words = re.findall(r'\b\w+\b', letter_text.lower())

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
    valid_terms.update(['full', 'stack', 'developer', 'web', 'api', 'data', 'development', 'team', 'work', 'experience'])

    # Check for potentially fake skills
    suspicious_terms = []
    for word in words:
        if len(word) > 3 and word not in valid_terms and not any(word in item.lower() for item in resume_skills['languages'] + resume_skills['frameworks'] + resume_skills['tools']):
            suspicious_terms.append(word)

    if suspicious_terms:
        issues.append(f"Potentially mock skills detected: {', '.join(suspicious_terms[:3])}")

    # Check for incorrect working years
    if 'years' in letter_text.lower() or any(char.isdigit() for char in letter_text):
        # Look for year patterns
        year_patterns = re.findall(r'\b\d+(?:\.\d+)?\s*(?:years?|yrs?)\b', letter_text.lower())
        for pattern in year_patterns:
            if '3' in pattern or '4' in pattern or '5' in pattern:
                issues.append(f"Incorrect working years detected: {pattern} (actual: ~2.6 years)")

    return issues


def compile_cl_tex(client, jd_text, company, title):
    main_tex_file = "./latex_cl/sample.tex"
    print("✍️ Generating CL LaTeX")

    letter, latex_content = write_cover_letter(
        client, main_tex_file, jd_text, company, title
    )

    print("✅ CL LaTeX generated successfully")
    return latex_content


def write_cover_letter(client, main_tex_file, jd_text, company, title):
    with open(main_tex_file, "r", encoding="utf-8") as f:
        tex_text = f.read()

    letter_body, formatted_letter = interactive_cover_letter_review(client, jd_text, company, title)

    # Inject into tex content
    new_tex = tex_text.replace("% Inject here", formatted_letter)

    return letter_body, new_tex


def interactive_cover_letter_review(client, jd_text, company, title):
    # Initial prompt for cover letter generation
    messages = [
        {
            "role": "system",
            "content": "You are a cover letter optimization agent using ReAct pattern. Generate authentic cover letters that align with job requirements using only verified candidate information. Never fabricate skills or exaggerate experience.",
        },
        {
            "role": "user",
            "content": cover_letter_prompt_template.format(
                jd_text=jd_text,
                company=company,
                title=title,
                name=os.getenv("NAME"),
                user_notes="",
            ),
        },
    ]

    review_history = []
    max_review_attempts = 3
    letter_body = ""  # Initialize to avoid NameError if all attempts fail

    for attempt in range(max_review_attempts):
        print(f"\n🔄 Review Loop {attempt + 1}/{max_review_attempts}")

        # Step 1: Generate candidate cover letter
        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=messages,
            )
            letter_body = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Generation error: {e}")
            continue

        # Step 2: Verify the letter for authenticity
        issues = verify_cover_letter(letter_body)
        review_history.append({
            'attempt': attempt + 1,
            'letter': letter_body,
            'issues': issues,
            'accepted': False
        })

        print("\n📄 Generated cover letter:")
        print(letter_body)
        print(f"🔍 Issues Found: {len(issues)}")

        if issues:
            print(f"⚠️  Issues: {', '.join(issues)}")
        else:
            print("✅ Verification Passed!")

        # If running in a non-interactive environment (e.g. Docker container / background task),
        # automatically accept the generated letter. Otherwise prompt the user.
        if sys.stdin is None or not sys.stdin.isatty():
            user_input = ""
            print("\nℹ️ Non-interactive environment detected — automatically accepting the cover letter.")
        else:
            user_input = input("\n📝 Press Enter to accept, or type suggestion: ").strip()

        # Step 3: If accepted, return the result
        if not user_input:
            print("🎉 Cover letter accepted!")
            formatted_paragraphs = [
                line.strip() for line in letter_body.split("\n") if line.strip()
            ]
            formatted_letter = "\n\n\\vspace{0.5cm}\n\n".join(formatted_paragraphs)
            return letter_body, formatted_letter

        # Step 4: If suggestions provided, add to conversation and regenerate
        if attempt < max_review_attempts - 1:
            # Add current letter and user feedback to conversation history
            messages.append({"role": "assistant", "content": letter_body})
            messages.append({"role": "user", "content": f"USER FEEDBACK: {user_input}\n\nPlease revise the cover letter based on this feedback."})

            print(f"🔧 Feedback received, regenerating...")
            review_history[-1]['feedback'] = user_input

    # If all attempts used, return the last letter with warning or raise error if no letter was generated
    print("⚠️  Maximum review attempts reached. Returning last version.")
    if not letter_body:
        raise Exception("Failed to generate cover letter after maximum attempts. Please check OpenAI API configuration and try again.")

    formatted_paragraphs = [
        line.strip() for line in letter_body.split("\n") if line.strip()
    ]
    formatted_letter = "\n\n\\vspace{0.5cm}\n\n".join(formatted_paragraphs)
    return letter_body, formatted_letter
