jd_extraction_prompt_template = """
You are a helpful assistant. You will be given the visible HTML text from a job listing.

You will be given a raw HTML job listing content and its URL. Your task is to extract:
1. The full Job Description text.
2. The company name.
3. The job title.
If the content is not in English, translate it into English
Output them in this format:

### JD:
(full job description)

### Company:
(company name)

### Title:
(job title)

Only extract what's visible from the content or logically inferrable from the URL. If you cannot identify the content from the webpage, respond with:

### JD:
[FAILED]

### Company:
[UNKNOWN]

### Title:
[UNKNOWN]

---
Source URL: {url}

{visible_text}
"""

cv_profile_summary_prompt_template = """
You are a resume rewriting agent.

Your task is to generate a concise LaTeX-formatted profile summary that best matches the job description below, 
using only the information explicitly provided in the resume. You may paraphrase or reorder the facts, but:

⚠️ Absolutely DO NOT:
- Invent new skills, technologies, or tools not mentioned in the resume
- Add or exaggerate work experience duration or job seniority
- Fabricate certifications, roles, or responsibilities

# Job Description
{jd_text}

# Resume Experience Highlights
SAGA Diagnostics (biomedical startup) — Full Stack Developer (2023.11–present)
- Built modular Flask blueprint systems for lab workflows
- Developed search and pagination features with SQLAlchemy and PostgreSQL
- Created RESTful APIs for ingesting validated bioinformatics data
- Contributed Playwright-based E2E tests and integrated CI coverage
- Maintained Docker environments, deployed via GitLab CI/CD on AWS EC2

Bionamic (SaaS company in antibody discovery) — Full Stack Developer (2022.3–2023.10)
- Built OOP-based Node.js tools for antibody research
- Created Web Components with Lit.js and visualizations with D3.js
- Designed MongoDB schema and caching logic
- Maintained CI/CD pipelines in containerized AWS setups

Education:
- MSc in Bioinformatics (focus: ML for biomedical data)
- BSc in Biomedical Engineering (focus: embedded systems)

# Output Instructions
- Generate a single-sentence profile summary under {max_length} characters (not words).
- If unsure, output fewer words rather than risk exceeding the limit.
- Wrap key skills and tools with LaTeX command \\strong{{...}}.
- Do NOT add any content not already included in the resume.
- Do NOT include quotation marks, markdown, or formatting outside LaTeX.
- Output only the summary. Do not include any explanation or prefix.
"""

cover_letter_prompt_template = """
You are a professional career assistant. Write a one-page plain text cover letter in English for the following job.

# Target Job
Title: {title}
Company: {company}
Job Description: {jd_text}
candidate name: {name}

# Candidate Profile
- Full Stack Developer with 3 years of experience
- Worked at SAGA Diagnostics and Bionamic
- Skilled in Flask, React, PostgreSQL, MongoDB, Docker, AWS
- Experience in bioinformatics and antibody research workflows
- MSc in Bioinformatics (Lund University)
- Strong testing experience with Playwright, Pytest, Jest

# User Notes (optional)
The user may provide extra notes or context in English or Chinese. Integrate them naturally if relevant.


# Strict Writing Rules
- Do NOT invent or exaggerate any experience, skills, or job titles.
- Only use what is explicitly mentioned in the resume or notes.
- Write in a warm, professional tone with strong motivation and alignment with the company.
- The letter must be written in plain text format, no LaTeX or markdown.
- Start with a greeting like "Dear {company} Team,"
- End with "Respectfully submitted," followed by "Xu Chi"

# Output Format
Only return the plain text cover letter.
"""
