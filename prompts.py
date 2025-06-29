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

summary_rewrite_prompt_template = """
You are a resume rewriting agent. Your task is to write the candidate's profile summary
so that it best matches the job description below — but only by rephrasing or reordering what
already exists in the resume. Do NOT invent or exaggerate skills, tools, or responsibilities.

# Job Description
{jd_text}

# Resume Experience Highlights
SAGA diagnostics a biomedical start up, 2023.11 - present
full stuck developer
- Built modular Flask blueprint-based systems for lab workflows at SAGA
- Developed search pages and pagination using SQLAlchemy and PostgreSQL
- Created RESTful APIs for ingesting validated bioinformatics data
- Contributed Playwright-based E2E tests integrated into CI pipelines
- Maintained Docker setups, deployed with GitLab CI/CD to AWS EC2

Bionamic a SAAS start up focusing on LIMS for antibody discover, 2022.3 - 2023.10
full stuck developer
- At Bionamic, built OO-based Node.js tools for antibody research
- Used Lit.js to build Web Components and interactive UIs
- Created D3.js visualizations for biological data exploration
- Used MongoDB with flexible schema and caching strategies
- Worked on CI/CD in a containerized AWS setup

- MSc in Bioinformatics (machine learning on biomedical data)
- BSc in Biomedical Engineering with embedded systems experience

# Output Instructions
- Rewrite the profile summary to better match the job description.
- The result must be under 300 characters (not words).
- Highlight key skills, tools, and areas of strength using LaTeX format: wrap them in \\strong{{...}}.
- Do not fabricate or exaggerate. Only use what is already in the resume.
- Do not include quotation marks or markdown.
"""
