# Kiron CV 🦕

**One application. One click. Kiron does the rest.**

> A local-first, end-to-end AI application engineered as a conventional software project and deployed as independent production services.

Kiron CV is a free, non-commercial AI application that turns a job offer and a candidate's career material into two practical application documents:

- a job-targeted, ATS-conscious two-page CV
- an honest job-match assessment

The complete workflow is automated and the finished documents are delivered by email.

---

## Built locally, end to end

Kiron was developed locally in **VS Code** as a conventional software engineering project.

It was **not generated inside a hosted AI application-building platform**. The application was designed and implemented as an explicit codebase with separate source files, dependencies, prompts, schemas, tests, runtime environments, API boundaries, document-generation stages, and deployment services.

AI-assisted development was used as part of the engineering workflow, but the application architecture, source code, testing, integration, debugging, and deployment remain explicit and locally controlled.

The development workflow followed a simple principle:

**design → implement locally → verify → integrate → test → deploy → verify again in production**

The same project can therefore be understood, modified, tested, and run as software rather than existing only inside a proprietary application builder.

---

## Technical environment

### Local development

- **Editor / workspace:** VS Code
- **Source control:** Git + GitHub
- **Backend environment:** Python virtual environment (`.venv`)
- **Frontend package manager:** pnpm 11.20
- **PDF service runtime:** Node.js >= 22.12
- **Configuration:** environment variables and local `.env`
- **Architecture:** modular monorepo with independently deployable services

### Frontend

- TypeScript 5.7
- Next.js 16.3
- React 19
- React DOM 19
- Tailwind CSS 4
- Base UI
- Lucide React
- Vercel Analytics
- PostCSS

The frontend is component-based: individual sections and responsibilities live in separate source files so that the interface can be modified without treating the application as one monolithic page.

### Python backend

- Python
- FastAPI 0.141.1
- Pydantic 2.13.4
- Google GenAI SDK 2.17.0
- Uvicorn 0.52.1
- python-dotenv 1.2.2

The backend owns request validation, AI orchestration, document-generation workflow, temporary job data, PDF coordination, and final email delivery.

### AI layer

Kiron currently uses the **Google Gemini API** through the official Google GenAI Python SDK.

The model is not treated as the application itself. It is one component behind an explicit AI layer containing:

- task-specific prompts
- model configuration
- structured outputs
- validation
- retry handling
- job orchestration
- separate processing stages

This separation makes the AI provider replaceable without requiring the rest of the application to be redesigned around one model API.

### PDF rendering service

PDF generation runs as a separate Node.js service using:

- Node.js >= 22.12
- Puppeteer Core
- `@sparticuz/chromium`

The Python backend sends completed HTML to the rendering service, which runs Chromium and returns the generated PDF.

Separating Chromium from the Python backend keeps browser-rendering dependencies out of the AI service and gives each runtime one clear responsibility.

---

## Production architecture

Kiron is deployed as **three cooperating services** rather than one oversized application:

```text
User's browser
      │
      ▼
┌─────────────────────┐
│  Next.js Frontend   │
│  TypeScript / React │
└──────────┬──────────┘
           │ HTTPS / JSON
           ▼
┌─────────────────────┐
│   FastAPI Backend   │
│       Python        │
└──────────┬──────────┘
           │
           ├──► Gemini API
           │      AI reasoning
           │
           ▼
     Structured data
           │
           ▼
      HTML generation
           │
           │ HTTPS
           ▼
┌─────────────────────┐
│    PDF Service      │
│ Node.js / Chromium  │
│ Puppeteer Core      │
└──────────┬──────────┘
           │
           ▼
      Two PDF files
           │
           ▼
       Gmail SMTP
           │
           ▼
        User inbox
```

### Service responsibilities

**Frontend**

Collects the job offer, career material, email address, and privacy acknowledgement. It validates the form and submits the application request to the backend.

**Backend**

Validates the request and runs the complete Kiron pipeline: hiring-criteria analysis, candidate evaluation, targeted CV generation, HTML generation, PDF coordination, email delivery, and temporary-data cleanup.

**PDF service**

Runs the Chromium environment required to convert Kiron's controlled HTML/CSS documents into real PDF files.

This separation was also a deployment engineering decision. Chromium/Puppeteer has very different runtime requirements from the Python AI pipeline, so separating the services keeps deployment boundaries explicit and independently testable.

---

## Production verification

Kiron was first developed and tested locally before deployment.

The deployed application was then verified through the **actual public browser interface**, not only through isolated API tests.

The verified production path is:

```text
Public frontend
      ↓
FastAPI backend
      ↓
Gemini AI pipeline
      ↓
Structured outputs
      ↓
HTML generation
      ↓
Remote Chromium PDF service
      ↓
Evaluation PDF + targeted CV PDF
      ↓
Gmail delivery
      ↓
User inbox
```

A real application submitted through the deployed frontend successfully completed the entire workflow and delivered both PDFs by email.

This production end-to-end test is the final ground truth that the independently deployed components communicate correctly.

---

## Why this project exists

Many CV platforms still require the user to spend a long time inside the application: selecting templates, rewriting sections, moving content, adjusting layouts, fixing formatting, and repeatedly deciding what belongs where.

Adding an LLM does not automatically solve that problem.

A useful CV system has to solve several connected problems at the same time:

- What matters for this particular job?
- Which parts of the candidate's experience are genuinely relevant?
- How should that experience be expressed without inventing information?
- How much content belongs in the document?
- How can that content fit a stable, readable layout?
- What should a recruiter understand in the first few seconds?

Kiron treats these as one engineering and design problem rather than a collection of separate features.

The goal is not simply to *generate text*. The goal is to create a useful application document automatically.

---

## One-click automation

The user provides three things:

1. the job offer
2. their CV / career material
3. an email address

After that, Kiron takes over.

Behind one action, the application runs the complete workflow:

**Job offer → hiring criteria → candidate matching → targeted CV → document rendering → assessment → PDFs → email delivery**

The user does not need to manually move generated text into a template or repair the document afterward.

> **Automate the workflow, not just the writing.**

---

## Prompt engineering is part of the product

Kiron does not send one generic request to an AI model and accept whatever comes back.

The AI workflow was designed as a sequence of specialized tasks. Prompts, schemas, intermediate outputs, evaluation criteria, and retry behaviour were repeatedly tested against the usefulness of the resulting documents.

The pipeline separates responsibilities such as:

- understanding the employer's actual hiring criteria
- evaluating the candidate against those criteria
- selecting relevant evidence from the candidate's material
- generating a targeted CV
- producing a realistic application assessment

This makes prompt engineering part of the application's engineering architecture rather than an isolated block of text.

The quality of an AI product depends not only on which model it uses, but on **how the problem presented to that model has been designed**.

---

## Content and layout are one system

One of the most difficult parts of automated CV generation is the relationship between **meaningful content and physical document space**.

A template can look beautiful with sample text and immediately break when real content becomes longer. An AI can generate detailed, useful material and still produce an unusable CV if the document becomes crowded, unbalanced, or difficult to scan.

Kiron was designed around this constraint.

The generated content and the PDF layout were developed together so that the system can preserve useful information while producing a controlled two-page document.

### Page 1

Designed for the fast recruiter / HR scan.

The most important information should be visible quickly, with a clear hierarchy and minimal visual friction.

### Page 2

Provides greater professional and project depth for the reader who understands the role and wants evidence.

The aim is not maximum decoration or maximum information density. It is a deliberate balance between:

**ATS readability · human scanning · meaningful evidence · visual hierarchy · limited page space**

That balance is a central part of Kiron's design.

---

## Honest assessment

Kiron is not designed to tell every applicant that they are a perfect match.

Before sending the application, the matching pipeline examines the candidate's available evidence against the hiring criteria and produces a separate assessment.

The intention is to help the applicant understand both:

- where their application is strong
- where meaningful gaps remain

AI assistance is more useful when it supports decisions rather than simply producing optimistic language.

---

## Career material as a living source

Kiron encourages a different way of thinking about the traditional CV.

A person's complete professional history does not need to be squeezed permanently into one finished document. Instead, career material can exist as a **living source file** containing projects, roles, skills, education, achievements, certifications, and other useful evidence.

That source can grow over time.

For each application, Kiron can then select and reformulate the material that matters for that particular opportunity.

The project includes a prompt designed to help users build this reusable career-material file with an AI chat tool they already trust.

---

## Privacy and temporary processing

Kiron is currently a free, non-commercial application demo using the **Google Gemini Free Tier API** for AI processing.

Information submitted for an application is therefore sent to Google Gemini as part of the generation workflow. Users with privacy concerns should review the terms and data-handling policies applicable to the Gemini API Free Tier before submitting personal information.

Within Kiron's own workflow, application files are treated as temporary processing data.

Each request receives an isolated job workspace. After the generation and email-delivery workflow finishes, the request-specific temporary inputs and generated processing directory are automatically deleted.

API keys and email credentials are kept outside the source code through environment configuration and are excluded from Git.

---

## Engineering principles

Kiron was developed around a small set of engineering rules:

- **Ground truth before assumptions.**
- **One responsibility per component or processing stage.**
- **Small, testable modules.**
- **Structured intermediate data instead of uncontrolled text passing.**
- **Automation before repetitive manual work.**
- **Local development before production deployment.**
- **Verify each stage before integrating the next one.**
- **Test against actual runtime behaviour.**
- **Design and engineering should solve the same user problem.**

The intention is to keep the system understandable enough that individual stages can be inspected, tested, replaced, or improved independently.

---

## Repository architecture

The repository is organized around runtime responsibility:

```text
CV-Job-Matcher/
│
├── backend/
│   ├── actions/          # individual pipeline operations
│   ├── ai/               # model access, configuration and retry logic
│   ├── assets/           # Kiron document assets
│   ├── pipelines/        # end-to-end job orchestration
│   ├── templates/        # HTML/CSS document templates
│   └── main.py           # FastAPI application
│
├── frontend/
│   ├── app/              # Next.js routes
│   ├── components/       # reusable UI sections
│   └── public/           # frontend static assets
│
├── pdf-service/
│   ├── api/              # deployed PDF endpoint
│   └── test/             # PDF rendering tests
│
├── schemas/              # runtime AI prompts / schemas
│
├── tests/                # backend and integration verification
│
├── requirements.txt      # Python dependencies
└── README.md
```

The important architectural rule is:

> **One script or component should have one clear responsibility.**

That keeps the AI pipeline, document rendering, frontend, and deployment infrastructure independently understandable.

---

## Testing strategy

Kiron is tested at multiple boundaries rather than relying on one final manual test.

Examples include:

- Python module and pipeline tests
- AI-layer validation
- pipeline integration testing
- HTML generation verification
- real PDF signature/output validation
- Node PDF-renderer tests
- Next.js production builds
- backend health checks
- deployed API tests
- production browser-to-email end-to-end verification

The PDF service, for example, is tested to confirm that it produces an actual PDF rather than merely returning a successful HTTP response.

At milestones, the complete relevant workflow is tested again before deployment.

---

## Technology summary

**AI & pipeline**

Google Gemini API · Google GenAI SDK · multi-stage LLM workflow · prompt engineering · structured JSON outputs · schema-driven generation · model validation · retry handling · job orchestration

**Backend**

Python · FastAPI · Pydantic · Uvicorn · REST API · CORS · environment-based secrets · automated email delivery · temporary-file lifecycle management

**Document generation**

Structured CV data · HTML templating · CSS print layout · HTML-to-PDF rendering · Chromium · Puppeteer Core · two-page CV architecture · separate evaluation PDF · reusable Kiron visual assets

**Frontend**

Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 · responsive UI · component architecture · client-side validation · privacy acknowledgement · API submission states

**Development & deployment**

VS Code · Git · GitHub · Python virtual environments · pnpm · Node.js · environment configuration · modular monorepo · independently deployed frontend/backend/PDF services

---

## Current status

**Production end-to-end workflow: verified.**

Kiron currently supports the complete public workflow:

**Browser submission → FastAPI → AI pipeline → document generation → remote PDF rendering → two PDFs → email delivery → temporary-data cleanup**

The frontend, backend, and PDF renderer operate as separate deployed services.

The application has been verified with a real submission through the public frontend and successful delivery of both generated PDF documents by email.

---

## Why Kiron?

Kiron CV grew from the experience of the Kiron THRIVE program and from seeing how difficult it can be to present professional experience when entering a new job market, changing direction, or rebuilding a career in a new country.

It is not a commercial product.

It is a small practical tool built from gratitude and offered back.

**Built by Dany Grünewald — Kiron THRIVE participant, 2026.**