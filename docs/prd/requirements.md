# Requirements

## Functional Requirements (Revised MVP Scope)
*   **FR1:** The system must allow a user to submit a text-based topic query.
*   **FR2:** The system must allow a user to submit a URL of a news article as a query.
*   **FR3:** The system shall retrieve news articles from a curated list of high-quality news APIs.
*   **FR4:** For each retrieved source, the system shall check for a corresponding hash on the configured blockchain and flag the source as "verified" or "unverified".
*   **FR5:** The system shall generate a summary of the retrieved sources in a "Debate Format", presenting opposing views.
*   **FR6:** The UI must display a slider to explore political bias in the underlying sources.
*   **FR7:** The system shall highlight text segments in the summary as `Fact`, `Opinion`, or `Contradiction`.

## Non-Functional Requirements
*   **NFR1:** All software components must be free and open-source.
*   **NFR2:** The system must be deployable on the free tiers of Vercel and Supabase.
*   **NFR3:** The median response time for generating a summary for a typical query must be under 30 seconds.
*   **NFR4:** The user interface shall be a responsive web application.
*   **NFR5:** The frontend will be built with React, Tailwind CSS, and shadcn/ui.
*   **NFR6:** The backend will be built with Python/FastAPI.
*   **NFR7:** The system shall be developed with mock interfaces for the blockchain verification (FR4) and bias analysis (FR6) components. This allows for parallel development and end-to-end testing before the real, external-facing services are integrated.
*   **NFR8:** All serverless functions must implement structured JSON logging from the start, including a unique request ID, to allow for easier tracing of requests across the system.

---
