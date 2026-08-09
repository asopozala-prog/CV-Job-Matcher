# Kiron CV 🦕

**One application. One click. Kiron does the rest.**

Kiron CV is a free, non-commercial AI application that turns a job offer
and a candidate's career material into two practical application
documents:

-   a job-targeted, ATS-conscious two-page CV
-   an honest job-match assessment

The result is generated automatically and delivered by email.

Kiron was built around a simple idea: **AI-assisted CV creation should
reduce work for the applicant, not create another complicated platform
they have to learn and manage.**

------------------------------------------------------------------------

## Why this project exists

Many CV platforms still require the user to spend a long time inside the
application: selecting templates, rewriting sections, moving content,
adjusting layouts, fixing formatting, and repeatedly deciding what
belongs where.

Adding an LLM does not automatically solve that problem.

A useful CV system has to solve several connected problems at the same
time:

-   What matters for this particular job?
-   Which parts of the candidate's experience are genuinely relevant?
-   How should that experience be expressed without inventing
    information?
-   How much content belongs in the document?
-   How can that content fit a stable, readable layout?
-   What should a recruiter understand in the first few seconds?

Kiron treats these as one engineering and design problem rather than a
collection of separate features.

The goal is not simply to *generate text*. The goal is to create a
useful application document automatically.

------------------------------------------------------------------------

## One-click automation

The user provides three things:

1.  the job offer
2.  their CV / career material
3.  an email address

After that, Kiron takes over.

Behind one action, the application runs the complete workflow:

**Job offer → hiring criteria → candidate matching → targeted CV →
document rendering → assessment → PDFs → email delivery**

The user does not need to manually move generated text into a template
or repair the document afterward.

> **Automate the workflow, not just the writing.**

------------------------------------------------------------------------

## Prompt engineering is part of the product

Kiron does not send one generic request to an AI model and accept
whatever comes back.

The AI workflow was designed as a sequence of specialized tasks.
Prompts, schemas, intermediate outputs, evaluation criteria, and retry
behaviour were repeatedly tested against the usefulness of the resulting
documents.

The pipeline separates responsibilities such as:

-   understanding the employer's actual hiring criteria
-   evaluating the candidate against those criteria
-   selecting relevant evidence from the candidate's material
-   generating a targeted CV
-   producing a realistic application assessment

This makes prompt engineering part of the application's engineering
architecture rather than an isolated block of text.

The quality of an AI product depends not only on which model it uses,
but on **how the problem presented to that model has been designed**.

------------------------------------------------------------------------

## Content and layout are one system

One of the most difficult parts of automated CV generation is the
relationship between **meaningful content and physical document space**.

A template can look beautiful with sample text and immediately break
when real content becomes longer. An AI can generate detailed, useful
material and still produce an unusable CV if the document becomes
crowded, unbalanced, or difficult to scan.

Kiron was designed around this constraint.

The generated content and the PDF layout were developed together so that
the system can preserve useful information while producing a controlled
two-page document.

### Page 1

Designed for the fast recruiter / HR scan.

The most important information should be visible quickly, with a clear
hierarchy and minimal visual friction.

### Page 2

Provides greater professional and project depth for the reader who
understands the role and wants evidence.

The aim is not maximum decoration or maximum information density. It is
a deliberate balance between:

**ATS readability · human scanning · meaningful evidence · visual
hierarchy · limited page space**

That balance is a central part of Kiron's design.

------------------------------------------------------------------------

## Honest assessment

Kiron is not designed to tell every applicant that they are a perfect
match.

Before sending the application, the matching pipeline examines the
candidate's available evidence against the hiring criteria and produces
a separate assessment.

The intention is to help the applicant understand both:

-   where their application is strong
-   where meaningful gaps remain

AI assistance is more useful when it supports decisions rather than
simply producing optimistic language.

------------------------------------------------------------------------

## Career material as a living source

Kiron encourages a different way of thinking about the traditional CV.

A person's complete professional history does not need to be squeezed
permanently into one finished document. Instead, career material can
exist as a **living source file** containing projects, roles, skills,
education, achievements, certifications, and other useful evidence.

That source can grow over time.

For each application, Kiron can then select and reformulate the material
that matters for that particular opportunity.

The project includes a prompt designed to help users build this reusable
career-material file with an AI chat tool they already trust.

------------------------------------------------------------------------

## Privacy and temporary processing

Kiron is currently a free, non-commercial application demo using the
**Google Gemini Free Tier API** for AI processing.

Information submitted for an application is therefore sent to Google
Gemini as part of the generation workflow. Users with privacy concerns
should review the terms and data-handling policies applicable to the
Gemini API Free Tier before submitting personal information.

Within Kiron's own workflow, application files are treated as temporary
processing data.

Each request receives an isolated job workspace. After the generation
and email-delivery workflow finishes, the request-specific temporary
inputs and generated processing directory are automatically deleted.

API keys and email credentials are kept outside the source code through
environment configuration and are excluded from Git.

------------------------------------------------------------------------

## Engineering principles

-   **Ground truth before assumptions.**
-   **One responsibility per component or processing stage.**
-   **Small, testable modules.**
-   **Structured intermediate data instead of uncontrolled text
    passing.**
-   **Automation before repetitive manual work.**
-   **Verify each stage before integrating the next one.**
-   **Design and engineering should solve the same user problem.**

------------------------------------------------------------------------

## Technology

**AI & pipeline:** Google Gemini API · multi-stage LLM workflow · prompt
engineering · structured JSON outputs · schema-driven generation · model
validation · retry handling · job orchestration

**Backend:** Python · FastAPI · Pydantic · REST API · CORS ·
environment-based secrets · automated email delivery · temporary-file
lifecycle management

**Document generation:** structured CV data · HTML templating · CSS
print layout · HTML-to-PDF rendering · two-page CV architecture ·
separate evaluation PDF · reusable Kiron visual assets

**Frontend:** Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 ·
responsive UI · client-side validation · privacy acknowledgement · API
submission states

**Development & packaging:** pnpm · Python virtual environments · Docker
· Git · environment configuration · modular project structure

------------------------------------------------------------------------

## Current status

The complete application workflow has been verified locally end to end:

**Browser submission → FastAPI → AI pipeline → document generation → two
PDFs → email delivery → automatic temporary-data deletion**

The frontend also passes a production Next.js build.

Public deployment is the next stage of the project.

------------------------------------------------------------------------

## Why Kiron?

Kiron CV grew from the experience of the Kiron THRIVE program and from
seeing how difficult it can be to present professional experience when
entering a new job market, changing direction, or rebuilding a career in
a new country.

It is not a commercial product.

It is a small practical tool built from gratitude and offered back.

**Built by Dany Grünewald --- Kiron THRIVE participant, 2026.**
