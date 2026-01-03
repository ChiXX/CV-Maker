# 🧠 CV Maker - Auto CV Generator

Automatically customize your LaTeX CV based on a job listing URL. This tool extracts job descriptions using AI, rewrites your profile summary to match the role, and generates LaTeX source files stored in a database. Now built as a FastAPI application for programmatic access and easy integration.

## ✅ Features

- **FastAPI Backend**: RESTful API for job application processing and management
- **AI-Powered Extraction**: Extracts job description, company, and title from URLs using OpenAI
- **Custom CV Generation**: Rewrites your CV summary using only content from your existing resume
- **LaTeX Generation**: Generates job-targeted LaTeX source files for CVs and cover letters
- **Database Storage**: Stores application data and generated LaTeX in PostgreSQL
- **RESTful Endpoints**: Programmatic access to create, read, and manage applications
- **Automatic Documentation**: Built-in API documentation with Swagger UI

## 🛠️ Requirements

- Python 3.12+
- Docker (for PostgreSQL database)
- `just` command runner (optional, for easier command management)
- OpenAI API access for job description extraction and content generation

### Python Dependencies
```bash
uv sync
```

### Frontend Dependencies
```bash
cd frontend && npm install
```

### Optional Tools
Install `just` command runner:
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

## 🌐 Web Interface

The web interface provides a modern UI for:
- **Job URL Input**: Submit job posting URLs through a clean form
- **Real-time Chat**: Monitor extraction and generation progress
- **LaTeX Downloading**: Download generated LaTeX source files for CVs and cover letters
- **Application History**: Browse all your generated applications

### Architecture
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with background task processing
- **Database**: PostgreSQL for application storage
- **LaTeX Generation**: LaTeX templates with AI-customized content

### API Endpoints
- `POST /applications/` - Create new application from job URL
- `GET /applications/` - List all applications with pagination
- `GET /applications/{id}` - Get specific application details
- `DELETE /applications/{id}` - Delete an application
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## 🚀 Quick Start

### FastAPI Server
Start the FastAPI application:

```bash
# Install dependencies
uv sync

# Start PostgreSQL database
docker-compose up -d

# Initialize database
python init_db.py

# Start the FastAPI server
python app.py

# Or using the script entry point
cv-maker

# Access API docs at http://localhost:8000/docs
```

### API Usage Example
```bash
# Create a new application
curl -X POST "http://localhost:8000/applications/" \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://example.com/job-posting"}'

# List all applications
curl "http://localhost:8000/applications/"
```

## 📋 Available Just Commands

### Full Stack Commands
- `just stack-up` - Start all services (database, API, frontend)
- `just stack-down` - Stop all services
- `just stack-logs` - View logs from all services

### Development Commands
- `just dev-setup` - Full development environment setup (Python + DB)
- `just frontend-install` - Install frontend dependencies
- `just frontend-dev` - Start frontend development server
- `just frontend-build` - Build frontend for production

### CLI Commands
- `just run` - Start the CLI CV generator
- `just run-cv <url>` - Generate CV for specific job URL
- `just api-run` - Start the API server only

### Database Commands
- `just db-start` - Start PostgreSQL database
- `just db-stop` - Stop database
- `just db-init` - Initialize database tables
- `just db-logs` - View database logs

### Utility Commands
- `just status` - Show current setup status
- `just sync` - Sync Python dependencies with uv
- `just clean` - Clean up generated files and cache

## 🚀 Running the Application

```bash
# Start the FastAPI server
python app.py

# Server will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### API Usage
Use the interactive API documentation at `/docs` or make direct API calls to create applications from job URLs. The API will extract job descriptions, generate customized LaTeX content, and store everything in the database.


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