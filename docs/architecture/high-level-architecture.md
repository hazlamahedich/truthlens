# High Level Architecture

## Technical Summary
The architecture for TruthLens is a modern, full-stack serverless solution designed for rapid development and scalability. The frontend will be a mobile-first React/Next.js application, deployed on Vercel's edge network. The backend consists of a suite of independent, agent-based serverless functions, written in Python with FastAPI, also hosted on Vercel. Data will be stored in a MongoDB Atlas NoSQL database. This architecture directly supports our agile, epic-driven approach, allowing for modular development and deployment while leveraging the generous free tiers of our chosen platforms.

## Platform and Infrastructure Choice
*   **Platform:** Vercel and MongoDB Atlas.
*   **Key Services:**
    *   **Vercel:** Frontend Hosting, Serverless Functions (for backend agents), CI/CD.
    *   **MongoDB Atlas:** NoSQL Document Database.
    *   **Supabase:** Retained as an option for Authentication and File Storage if needed in the future.
*   **Deployment Host and Regions:** Vercel Edge Network (Global), MongoDB Atlas (Default Region, e.g., US East).
*   **Trade-offs:** We are consciously accepting a degree of platform lock-in with Vercel and MongoDB Atlas in exchange for a significant increase in development speed and a reduction in operational complexity for the MVP.

## Repository Structure
*   **Structure:** Monorepo.
*   **Monorepo Tool:** We will use the structure provided by the **Vercel Next.js Enterprise Boilerplate**, which is powered by Turborepo.
*   **Package Organization:** The monorepo will contain an `apps/` directory for the deployable applications (e.g., `web` for the frontend, `api` for the backend functions) and a `packages/` directory for shared code (e.g., `shared-types`, `ui-components`).

## High Level Architecture Diagram
```mermaid
graph TD
    subgraph User
        U[Skeptical Verifier]
    end

    subgraph Vercel Platform
        subgraph Frontend
            WebApp[React/Next.js App]
        end
        subgraph Backend (Serverless Functions)
            Orchestrator[Orchestrator Agent]
            Retrieval[Retrieval Agent]
            Verification[Verification Agent]
            Summarization[Summarization Agent]
        end
    end

    subgraph Cloud Services
        DB[(MongoDB Atlas)]
    end

    subgraph External Services
        NewsAPIs[News APIs]
        Blockchain[Blockchain Node]
        LLM[LLM API]
    end

    U --> WebApp;
    WebApp --> Orchestrator;
    Orchestrator --> Retrieval;
    Orchestrator --> Verification;
    Orchestrator --> Summarization;
    Retrieval --> NewsAPIs;
    Verification --> Blockchain;
    Summarization --> LLM;
    Orchestrator --> DB;
```

## Architectural Patterns
*   **Serverless Architecture:** The backend will be composed of independent, stateless functions that execute on demand. _Rationale:_ This is cost-effective, highly scalable, and aligns perfectly with our "free tier" constraint.
*   **Monorepo:** All code for the frontend, backend, and shared packages will reside in a single repository. _Rationale:_ Simplifies dependency management and cross-cutting changes for a small team.
*   **Agent-Based Modules:** Each core backend capability will be a logically separate agent (a serverless function). _Rationale:_ This enforces separation of concerns and allows for independent development and testing.
*   **Mobile-First Design:** The user interface will be designed for a mobile experience first, then adapted for desktop. _Rationale:_ This prioritizes the platform where our target users are most active.

---
