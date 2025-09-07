# Epic 1 Details: The First Verifiable Summary

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
