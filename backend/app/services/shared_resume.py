# Shared resume data for both CV and Cover Letter generation
resume_data = {
    "languages": ["Python", "Node.js", "JavaScript", "TypeScript", "C/C++"],
    "frameworks": [
        "Flask",
        "SQLAlchemy",
        "Lit.js",
        "D3.js",
        "React",
        "Next.js",
        "jQuery",
        "Bootstrap",
    ],
    "databases": ["PostgreSQL", "MongoDB"],
    "tools": [
        "Docker",
        "GitLab CI/CD",
        "GitHub Actions",
        "AWS",
        "Playwright",
        "Jinja2",
    ],
    "experience": {
        "Total Working Experience": "4 years",
        "SAGA Diagnostics": 
"""Full Stack Developer | 11/2023 - 09/2025
Architected and engineered an end-to-end dPCR (Digital PCR) automation and laboratory information management ecosystem, successfully reducing manual data processing time by 50% while ensuring 100% clinical-grade data traceability.

- B2B Integration & Workflow Automation: Revolutionized the procurement workflow by developing an automated B2B ordering module. Replaced manual, error-prone web entries with a "one-click" bulk ordering system using XML protocols, achieving a 10x increase in efficiency (ordering 10+ plates simultaneously). Integrated AWS S3 for persistent storage and versioning of order metadata, creating a closed-loop audit trail from procurement to analysis.

- Scalable Backend Architecture: Engineered a highly flexible data model using SQLAlchemy Polymorphism (Joined Table Inheritance) to manage the complex lifecycle of primer and nano plates. Designed a schema-driven configuration system that allows for the dynamic loading of plate layouts; this decoupled the software logic from physical hardware specifications, enabling the lab to adopt new plate models via S3 configuration updates without requiring code redeployment.

- High-Throughput Data Engineering: Optimized PostgreSQL performance to handle the multi-layered hierarchy of genomic data (Plate → Well → Target → Channel). Leveraged SQLAlchemy bulk mappings and index optimization to facilitate the seamless ingestion of tens of thousands of records per run, ensuring real-time system responsiveness during high-volume sequencing cycles.

- Interactive Scientific Visualization: Developed a high-performance interactive dashboard using D3.js and HTMX/Jinja macros. Created custom visualizations for dPCR signal distributions and patient-centric analysis trends, enabling researchers to perform manual Quality Control (QC) through intuitive drag-and-drop and selection interfaces. This solution significantly outperformed legacy Excel-based methods in both rendering speed and analytical insight.

- Compliance & Security: Implemented a robust Role-Based Access Control (RBAC) system and a comprehensive Audit Trail architecture. By recording the full history of data mutations (Create/Update/Delete), the system met stringent EU clinical data standards, ensuring that all laboratory operations are transparent, secure, and ready for regulatory auditing.
""",
        "Bionamic": 
"""Full Stack Developer | 03/2022 - 10/2023 (Lund, Sweden)

Engineered high-performance web applications for antibody discovery, focusing on complex biological data visualization and hierarchical data management.

Lightweight Frontend Architecture: Leveraged Web Components (Lit.js) to develop a high-performance, lightweight Single Page Application (SPA). By utilizing native browser capabilities, reduced bundle sizes and improved rendering speeds for data-heavy interfaces compared to traditional frameworks.

Scientific Data Visualization: Utilized D3.js to create specialized biological visualizations, including high-throughput sequence alignment plots and force-directed network graphs. These tools enabled scientists to analyze topological relationships between antibody candidates and visualize mutations across large libraries.

Hierarchical Data Modeling & Caching: Architected a Node.js (OOP) backend to manage the complex, multi-level hierarchy of antibody lineages (Library → VHVL → Purified Antibody). Implemented a MongoDB-based caching layer to store these recursive indexing relationships, drastically reducing the latency of deep-nested data retrieval and cross-entity lookups.

Dynamic Data Exploration Tools: Designed and implemented a proprietary "Relational Data Grid" featuring dynamic join-like functionality. This allowed researchers to perform real-time data exploration by dynamically injecting related antibody columns into active library views, significantly streamlining the "Hit Selection" process.

Cloud Infrastructure & Reliability: Managed containerized deployment pipelines using Docker on AWS EC2. Enhanced system stability by establishing a comprehensive automated testing suite, ensuring reliable data ingestion and consistent visualization performance across iterative software releases.
""",
        "Region Skåne": 
"""Software Developer | 10/2025 - 4/2026 (Lund, Sweden)

Orchestrating high-reliability data exchange and infrastructure modernization for regional hospital-LIMS (Laboratory Information Management System) integrations.

Architectural Refactoring & Standardization: Spearheaded the refactoring of a mission-critical Python data service by implementing the Factory Pattern. Successfully consolidated dozens of redundant, hospital-specific scripts into a unified interface, utilizing abstracted data-mapping methods to handle heterogeneous input formats. This modular approach transformed a legacy "if-else" codebase into a scalable framework, allowing new data formats to be integrated with minimal overhead through standardized templates.

Middleware Engineering & Semantic Mapping: Developed a robust middleware solution for weekly cross-system synchronization. Navigated complex semantic discrepancies between independent engineering teams to establish a unified data dictionary, ensuring high fidelity during transformation. Implemented a fault-tolerant "backfill" mechanism that automatically re-scans and populates missing records within valid time windows, coupled with comprehensive step-level logging to guarantee data integrity.

Containerized DevOps Strategy: Managed a large-scale legacy module hosting multiple sub-projects with conflicting environment requirements. Optimized deployment workflows by implementing container versioning strategies, allowing distinct projects to run in isolated, version-controlled environments. Integrated GitHub Actions with semantic tagging to automate the lifecycle from unit testing to stable container release, drastically reducing deployment downtime.

Operational Visual Analytics: Designed and deployed interactive Plotly dashboards for laboratory personnel, enabling real-time comparative analysis of sequencing runs. This tool transformed raw sequencing metrics into actionable insights, allowing operators to detect anomalies and compare performance across different batches instantly.
""",
        "Education": 
"""MSc in Bioinformatics | Lund University | 08/2019 - 02/2022

Master's Thesis (Predictive Modeling): Developed advanced feature selection pipelines for RNA-seq data to predict patient survival outcomes. Focused on transcript-level (isoform) analysis using Machine Learning to identify high-resolution prognostic biomarkers. \faLink

Batch Effect Diagnostics: Engineered an ML-driven framework to detect and quantify batch effects in proteomics data. Utilized statistical learning to ensure data robustness and reproducibility in large-scale high-throughput biological experiments. \faLink

Cancer Genomics (Lung Cancer Project): Conducted multi-omic data analysis to model Lung Cancer progression. Applied statistical modeling and classification algorithms to genomic datasets to extract clinically relevant signatures for patient stratification. \faLink

Core Competencies: Specialized in applying Deep Learning and Statistical Inference to biomedical challenges, bridging the gap between raw sequencing data and clinical insights.
""",
        "Education": "BSc in Biomedical Engineering (embedded systems focus)",
    },
    "projects": {
        "AI Agent based CV auto-generator": "An advanced agentic AI system utilizing LangGraph to orchestrate a multi-agent workflow (Parsing, Matching, and Optimization) for personalized resume generation. It features a stateful architecture to handle complex task dependencies and an asynchronous FastAPI backend to manage high-concurrency LLM interactions.",
        "TODO App with MERN stack": "A production-grade task management platform demonstrating industrial software engineering standards. It features a robust Test-Driven Development (TDD) suite using Jest, full containerization via Docker for environment consistency, and optimized frontend performance through custom pagination and state management.",
        "Lung Cancer Multi-omic Analysis": "A comprehensive bioinformatics research project applying statistical modeling and classification algorithms to multi-omic datasets. The project focused on modeling cancer progression and extracting clinically relevant genomic signatures for high-accuracy patient stratification.",
        "RNA-seq Isoform Feature Selection Pipeline": "A high-resolution predictive modeling pipeline developed for my Master's thesis, utilizing Machine Learning for transcript-level (isoform) analysis of RNA-seq data. It identifies prognostic biomarkers and optimizes feature selection for patient survival outcome prediction.",
        "Proteomics Batch Effect Detection": "An ML-driven diagnostic framework designed to detect, quantify, and mitigate batch effects in high-throughput proteomics experiments. This project ensures technical robustness and scientific reproducibility by applying statistical learning to large-scale biological datasets."
    }
        
}
