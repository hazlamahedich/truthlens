# TruthLens Product Requirements Document (PRD)

## Goals and Background Context

### Goals
*   To validate that users find value in a news summarization tool that offers integrated blockchain-based source verification.
*   To prove that interactive tools for exploring bias lead to higher user engagement and trust compared to static summaries.
*   To build a foundational, modular platform with an agentic architecture that can be easily extended with new technologies and features in the future.
*   To achieve an initial user base of 1,000 monthly active "Skeptical Verifiers" who demonstrate high retention rates.

### Background Context
The current media landscape is characterized by information overload and declining trust due to opaque biases and the proliferation of misinformation. Existing news aggregators fail to solve this as they typically only group articles, leaving the burden of verification and bias detection on the user. TruthLens addresses this gap by providing an integrated solution that automates source verification via the blockchain and allows users to interactively explore different viewpoints. This PRD outlines the requirements for the Minimum Viable Product (MVP) intended to prove the core value of this approach.

### Change Log

| Date       | Version | Description      | Author                |
| :--------- | :------ | :--------------- | :-------------------- |
| 2025-09-06 | 1.0     | Initial PRD draft | John, Product Manager |

---

## Requirements

### Functional Requirements (Revised MVP Scope)
*   **FR1:** The system must allow a user to submit a text-based topic query.
*   **FR2:** The system must allow a user to submit a URL of a news article as a query.
*   **FR3:** The system shall retrieve news articles from a curated list of high-quality news APIs.
*   **FR4:** For each retrieved source, the system shall check for a corresponding hash on the configured blockchain and flag the source as "verified" or "unverified".
*   **FR5:** The system shall generate a summary of the retrieved sources in a "Debate Format", presenting opposing views.
*   **FR6:** The UI must display a slider to explore political bias in the underlying sources.
*   **FR7:** The system shall highlight text segments in the summary as `Fact`, `Opinion`, or `Contradiction`.

### Non-Functional Requirements
*   **NFR1:** All software components must be free and open-source.
*   **NFR2:** The system must be deployable on the free tiers of Vercel and Supabase.
*   **NFR3:** The median response time for generating a summary for a typical query must be under 30 seconds.
*   **NFR4:** The user interface shall be a responsive web application.
*   **NFR5:** The frontend will be built with React, Tailwind CSS, and shadcn/ui.
*   **NFR6:** The backend will be built with Python/FastAPI.
*   **NFR7:** The system shall be developed with mock interfaces for the blockchain verification (FR4) and bias analysis (FR6) components. This allows for parallel development and end-to-end testing before the real, external-facing services are integrated.
*   **NFR8:** All serverless functions must implement structured JSON logging from the start, including a unique request ID, to allow for easier tracing of requests across the system.

---

## User Interface Design Goals

### Overall UX Vision
The UX should be immersive and opinionated, evoking the feeling of a **"digital detective's toolkit" or a "hacker's analysis console."** It must feel powerful and specialized, while remaining clear and usable. The goal is to build trust through a distinct, transparent, and controllable interface, moving beyond a generic "minimalist" aesthetic.

### Key Interaction Paradigms
*   **Query First:** The user journey begins with a clear, singular action: asking a question or providing a URL.
*   **Interactive Exploration:** The core of the app is not a static results page, but an interactive dashboard where users can manipulate the output via the bias slider.
*   **Drill-Down for Proof:** Users should always be one click away from the original source article and the blockchain verification record for any claim.

### Core Screens and Views (Revised MVP)
*   **Home/Query Screen:** A simple page with a prominent input field for text or URL queries.
*   **Results View:** The main screen displaying the generated "Debate Format" summary, the bias slider, and the highlighted text.
*   *(A dedicated 'Source List View' is deferred post-MVP. Source links will be accessible directly from the Results View.)*

### Accessibility
*   The application should meet **WCAG 2.1 AA** standards.

### Branding
*   The branding will align with the **"digital detective/hacker" theme**. This suggests a potentially darker theme with vibrant accent colors used for data visualization and highlighting. The goal is a unique and memorable identity.

### Target Platforms
*   The application will be designed with a **Mobile-First** philosophy. The core user experience will be perfected on mobile browsers first, and then adapted for larger desktop screens.

---

## Technical Assumptions

### Repository Structure: Monorepo
*   **Rationale:** For a solo developer or small team, a monorepo is simpler to set up and manage.

### Service Architecture: Serverless Functions
*   **Architecture:** The system will be built with a **Serverless** backend. Each agent will be developed as an independent, deployable serverless function.
*   **Rationale:** This architecture is ideal for our "free tier" constraint, as it only consumes resources on demand.

### Testing Requirements
*   **Strategy:** The MVP will require **Unit + Integration tests**.
*   **Rationale:** This provides a balanced approach to quality.

### Additional Technical Assumptions and Requests
*   **Frontend:** React.js, Tailwind CSS, shadcn/ui.
*   **Backend:** Python with FastAPI, leveraging its asynchronous capabilities.
*   **Database:** PostgreSQL (via Supabase).
*   **Deployment:** Vercel (frontend/serverless) and Supabase (database).
*   **Blockchain:** Polygon or an Ethereum Testnet.
*   **Initial Development Strategy:** Use mocked interfaces for blockchain and bias-analysis services.

---

## Epic List

*   **Epic 1: The First Verifiable Summary**
    *   **Goal:** Implement the absolute simplest end-to-end flow. A user can enter a text query and get back a single, simple paragraph summary with at least one source flagged as "verified" or "unverified".
*   **Epic 2: The Debate Format**
    *   **Goal:** Evolve the simple summary into the full, multi-perspective "Debate Format".
*   **Epic 3: The Interactive Bias Slider**
    *   **Goal:** Enhance the results view by adding the interactive political bias slider and fact/opinion highlighting.
*   **Epic 4: URL Query & MVP Polish**
    *   **Goal:** Add the ability for users to query by URL and conduct a final round of polishing and bug fixing.

---

## Epic 1 Details: The First Verifiable Summary

**Goal:** The objective of this epic is to implement the absolute simplest end-to-end functional slice of the application, proving the entire technical pipeline works correctly.

*   **Story 1.1: Local Development Setup**
    *   **AC:** Get frontend and backend running and communicating on the local development machine.
*   **Story 1.2: Initial Deployment**
    *   **AC:** Take the working local app and get it deployed via the CI/CD pipeline.
*   **Story 1.3: Secure API Key Configuration**
    *   **AC:** Establish and document the process for securely managing secrets using Vercel/Supabase environment variables.
*   **Story 1.4: Activate the Query**
    *   **AC:** A user can type a query into a real UI text box, which calls the backend and returns a mocked summary.
*   **Story 1.5: Activate Retrieval**
    *   **AC:** The Retrieval agent is built to handle a list of news APIs, and is configured with one live API. The rest of the pipeline remains mocked.
*   **Story 1.6: Activate Summarization**
    *   **AC:** The mocked Summarization agent is replaced with a real LLM call. The call must be behind a feature flag and gracefully handle errors.
*   **Story 1.7: Activate Verification**
    *   **AC:** The mocked Verification agent is replaced with the real (but initially mocked-as-per-NFR7) logic, and the UI correctly displays the "Verified"/"Unverified" status.

---

## Next Steps

This document is now ready to be handed off to the specialist agents.
*   The **UX Expert** can use the UI/UX Goals to begin creating wireframes and prototypes.
*   The **Architect** can use the Technical Assumptions and Epic breakdown to create a detailed system architecture document.
