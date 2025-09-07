# Data Models

## User
*   **Purpose:** Represents a user of the application. (Future-proofing for auth).
*   **TypeScript Interface:**
    ```typescript
    interface User {
      id: string; // a.k.a. sub from JWT
      email: string;
      createdAt: Date;
    }
    ```

## Query
*   **Purpose:** Represents a query made by a user and the resulting summary.
*   **TypeScript Interface:**
    ```typescript
    interface Query {
      id: string;
      userId?: string;
      queryText: string;
      summary: Summary;
      createdAt: Date;
    }
    ```

## Summary
*   **Purpose:** The structured summary output from the agents.
*   **TypeScript Interface:**
    ```typescript
    interface Summary {
      format: 'debate' | 'venn_diagram';
      content: any; // Flexible structure for different formats
      sources: Source[];
    }
    ```

## Source
*   **Purpose:** Represents a source article used in a summary.
*   **TypeScript Interface:**
    ```typescript
    interface Source {
      url: string;
      title: string;
      isVerified: boolean; // From blockchain check
      biasScore?: number; // Future use
    }
    ```

---