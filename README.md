# 🧠 Auto CV Generator

Automatically customize your LaTeX CV based on a job listing URL. This tool extracts job descriptions using a free LLM (via OpenRouter), rewrites your profile summary to match the role, and compiles the final PDF resume using `pdflatex`. Now includes database storage for tracking applications.

## ✅ Features

- Extracts job description, company, and title from a given URL
- Rewrites your CV summary using only the content from your existing resume
- Outputs a job-targeted PDF named `CV-{name}.pdf` and saves the JD as a `.txt` file
- All output stored in `Applications/{Company}-{Date}/`
- **NEW**: Stores application data and generated PDFs in PostgreSQL database

## 🛠️ Requirements

- Python 3.8+
- `pdflatex` installed
- Docker (for PostgreSQL database)
- `just` command runner (optional, for easier command management)
- Dependencies:
  - `openai`
  - `python-dotenv`
  - `beautifulsoup4`
  - `requests`
  - `sqlalchemy`
  - `psycopg2-binary`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install `just` command runner (optional):

```bash
# On Ubuntu/Debian
sudo apt install just

# On macOS
brew install just

# Or download from: https://github.com/casey/just/releases
```

## 🗄️ Database Setup

1. Start PostgreSQL using Docker Compose:

```bash
docker-compose up -d
```

2. The database will be available at `postgresql://cv_user:cv_password@localhost:5432/cv_maker`

3. Initialize the database tables:

```bash
python init_db.py
```

4. Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Then edit `.env` with your actual configuration values.

## 🚀 Quick Start with Just (Recommended)

If you have `just` installed, use these simple commands:

```bash
# Complete setup (database + dependencies)
just dev-setup

# Run the application
just run

# Or run with a specific job URL
just run-cv "https://example.com/job-url"
```

## 📋 Available Just Commands

- `just` - Show all available commands
- `just dev-setup` - Full development environment setup
- `just run` - Start the CV generator
- `just run-cv <url>` - Generate CV for specific job URL
- `just db-start` - Start PostgreSQL database
- `just db-stop` - Stop database
- `just db-init` - Initialize database tables
- `just status` - Show current setup status

## How to start

```bash
python main.py
```

Expected output:
```
🔗 请输入职位链接: https://bli.b3.se/jobs/932081-senior-system-developer?utm_source=LinkedIn
🌐 Fetching job page content: https://bli.b3.se/jobs/932081-senior-system-developer?utm_source=LinkedIn
🤖 Calling model to extract JD information
✅ Extraction completed → Company: B3 Consulting Group, Title: Senior System Developer
📁 Copying LaTeX project into temporary directory: /tmp/tmpezdjbi84
✍️ Summary updated in LaTeX file
This is pdfTeX, Version 3.141592653-2.6-1.40.22 (TeX Live 2022/dev/Debian) (preloaded format=pdflatex)
 restricted \write18 enabled.
entering extended mode
✅ Compilation complete. PDF saved to: Applications/B3 Consulting Group-2025-06-28
```


Example:

Job URL: https://bli.b3.se/jobs/932081-senior-system-developer?utm_source=LinkedIn

Summarized JD
```
B3 Skilled AB is the new name in the market and the result of a successful merger between B3 Third Base AB and B3 Nuway AB. We are proud of our long history in software development across various industries and numerous customers. We are delighted to be regularly recognized as one of Sweden's Career Companies and Rapid Growth Companies by Dagens Industri, reflecting our economic stability and growth.
B3 Skilled is part of B3 Consulting Group, Sweden's fastest-growing IT consultancy group. We are passionate about embracing a wide range of technologies, including Open Source, Android, iOS, Java, C#, C, C++, Node, Databases, IoT, and more.
We strive to create an inclusive and diverse work environment. Therefore, we are looking for someone with extensive experience in software development. If you share our passion for technology, are curious about embracing new challenges, and strive to always be at the forefront, you are exactly the person we want. We value diversity and would be happy if you were a team player with a customer focus, where problem-solving is your driving force. Together, we strive to be the best, and we believe you share that ambition with us!
We welcome applicants with various backgrounds and experiences and positively view a technical university education in systems science or engineering. Full-stack competence is essential for us, but we also view specialists in backend or cloud positively.
Experience in some of the following areas is appreciated:
- System development
- APIs
- Integration
- Working in an agile environment
- Working with operations and infrastructure (DevOps)
- Programming languages: C# (.NET), Java, Python
- Docker
- Kubernetes
- Cloud services: AWS, Azure, or GCP
- Jenkins
- GIT
We are committed to creating an inclusive work environment where everyone feels welcome and valued. We prioritize our employees above all else, and every decision we make is aimed at their well-being. We have created an inclusive, safe, and stable work environment with fantastic colleagues, beneficial benefits, and exciting assignments and customers.
- Competitive salary (We apply a fixed salary at B3 Skilled)
- Opportunities for relevant education and attractive certifications
- A comprehensive wellness and employee initiative. Read more here
- And above all, our team. We have secure owners and represent the "small" company in a large corporation. We are proud of the culture we have built up.
If you are interested, click on the application or do not hesitate to contact our responsible recruiter Lidia Hagos via
lidia.hagos@b3.se or
Consultant Manager Daniella Meyerson via
daniella.meyerson@b3skilled.se. We look forward to getting to know you!
```

Generated profile summary:
```
Full Stack Developer with 3 years of experience in system development, specializing in APIs and interac￾tive UIs. Proficient in Python, Flask, React, and PostgreSQL, with DevOps skills in Docker and AWS.
```