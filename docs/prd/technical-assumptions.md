# Technical Assumptions

## Repository Structure: Monorepo
*   **Rationale:** For a solo developer or small team, a monorepo is simpler to set up and manage.

## Service Architecture: Serverless Functions
*   **Architecture:** The system will be built with a **Serverless** backend. Each agent will be developed as an independent, deployable serverless function.
*   **Rationale:** This architecture is ideal for our "free tier" constraint, as it only consumes resources on demand.

## Testing Requirements
*   **Strategy:** The MVP will require **Unit + Integration tests**.
*   **Rationale:** This provides a balanced approach to quality.

## Additional Technical Assumptions and Requests
*   **Frontend:** React.js, Tailwind CSS, shadcn/ui.
*   **Backend:** Python with FastAPI, leveraging its asynchronous capabilities.
*   **Database:** PostgreSQL (via Supabase).
*   **Deployment:** Vercel (frontend/serverless) and Supabase (database).
*   **Blockchain:** Polygon or an Ethereum Testnet.
*   **Initial Development Strategy:** Use mocked interfaces for blockchain and bias-analysis services.

---
