# TruthLens UI/UX Specification

## Introduction

This document defines the user experience goals, information architecture, user flows, and visual design specifications for TruthLens's user interface. It serves as the foundation for visual design and frontend development, ensuring a cohesive and user-centered experience.

#### Overall UX Goals & Principles

*   **Target User Personas:**
    *   **The Skeptical Verifier:** A tech-savvy news consumer who is disillusioned with mainstream media, desires evidence-based reporting, and is willing to use tools to find a verifiable, multi-faceted understanding of events.

*   **Usability Goals:**
    *   **Rapid Insight:** A user should be able to go from query to understanding the core debate on a topic in under 60 seconds.
    *   **Trust & Verifiability:** Users should feel confident in the information presented and should be able to easily trace any claim back to its source.
    *   **Engaging Exploration:** The interface should encourage and reward curiosity, making the process of exploring different biases feel insightful, not like a chore.

*   **Design Principles (in order of priority):**
    1.  **Clarity in Complexity:** Our primary goal is to make confusing topics clear. When a design choice must be made, the clearest and simplest option will always be chosen.
    2.  **Transparency First:** Every piece of data should be traceable to its source.
    3.  **The User is in Control:** The interface provides powerful tools for exploration, not a single, static answer.
    4.  **Thematic, Not Obscuring:** The "digital detective" theme will be applied subtly through typography and micro-interactions, but must never compromise clarity.

#### Change Log
| Date       | Version | Description                    | Author          |
| :--------- | :------ | :----------------------------- | :-------------- |
| 2025-09-06 | 1.0     | Initial draft of Front-End Spec | Sally, UX Expert |

---

## Information Architecture

#### Site Map / Screen Inventory
```mermaid
graph TD
    subgraph Core App Flow
        A[Home / Query Screen] --> B[Results Dashboard]
    end
    subgraph Informational Pages (Static MVP)
        A --> C(About Page)
        A --> D(How It Works Page)
        A --> E(Feedback Page)
    end
```

#### Navigation Structure
*   **Primary Navigation:** The primary user flow is a linear two-step process (`Query -> Results`).
*   **Footer Navigation:** A simple footer menu will be present on the `Home/Query Screen` to provide access to the static informational pages.
*   **Content Ownership:** The Product Owner is responsible for maintaining the accuracy of the content on the informational pages.

---

## User Flows

### Flow: Main Query & Analysis
*   **User Goal:** To get a verifiable, multi-perspective summary of a news topic.
*   **Flow Diagram:**
    ```mermaid
    graph TD
        A[Start: User on Home Screen] --> B{Enters a text query};
        B --> C[Clicks 'Submit'];
        C --> D[UI enters Loading State];
        D --> E[Results Dashboard is displayed];
        subgraph E
            direction LR
            E1[Summary is shown by default]
            E2[Optional: User opens 'Sources' panel]
            E3[User de-selects a source]
            E4['Update Summary' button appears]
        end
        E4 --> F[User clicks 'Update Summary'];
        F --> G[UI shows subtle regeneration state];
        G --> E1;
    end
    ```

---

## Wireframes & Mockups

### Primary Design Files
*   Detailed wireframes, high-fidelity mockups, and interactive prototypes will be created and maintained in **Figma**.

### Key Screen Layouts
*   **Home/Query Screen:** A minimalist screen with a strong focus on the query input field.
*   **Results Dashboard:** A unified, dynamic screen. The summary is shown by default. A "Sources" panel (e.g., a sidebar or drawer) can be opened to view and de-select sources, which triggers a dynamic regeneration of the summary. The layout will be a single column on mobile and an enhanced multi-pane view on desktop.

---

## Component Library / Design System

### Design System Approach
*   We will use **shadcn/ui**. This provides the ideal balance of speed and control for our unique design goals.
*   **Maintenance Process:** A quarterly review of upstream `shadcn/ui` changes will be performed to incorporate bug fixes and security patches.
*   **Customization Guidelines:** All component customization will be governed by a `UI_GUIDELINES.md` document to ensure consistency.
*   **New Component Process:** Future features will include a "component audit" during design to plan for any required custom component development.

### Core Components
*   Button, Input, Checkbox, Slider, Loading Indicator.

---

## Branding & Style Guide

### Visual Identity
*   The application will support both a **Light Theme** (for maximum readability) and a **Dark Theme** (for thematic immersion), with a user-facing toggle. An inline script will be used to prevent the "flash of incorrect theme."

### Color Palette
*   The color palette will support both themes using CSS variables to ensure high contrast in both modes, meeting WCAG AA standards.

### Development Process
*   All UI components must be tested in both light and dark modes as part of their "Definition of Done."

---

## Accessibility Requirements

### Compliance Target
*   The application will meet **100% of WCAG 2.1 Level AA** requirements, and will strategically implement several Level AAA criteria to demonstrate leadership in accessibility.

### Key AAA Enhancements for MVP
*   **Enhanced Contrast (AAA):** All primary body text will meet the stricter 7:1 contrast ratio.
*   **Content Clarity (AAA):** Informational pages will be written for clarity and will include a glossary for technical terms.

---

## Responsiveness Strategy

### Adaptation Patterns
*   Our philosophy is **Mobile-First, with Desktop Enhancement.**
*   The layout will be a single column on mobile. On larger screens, the layout will be enhanced to become a multi-pane "dashboard."
*   Core components will be governed by a "Shared Component Logic" principle to ensure a consistent user experience across all devices.

---

## Animation & Micro-interactions

### Motion Principles
*   Animations will be purposeful, performant, and accessible.

### Key Animations
*   Standard transitions will be used for UI states. Thematic animations (e.g., "text decryption" loader) will be used subtly to enhance the brand, and their development is planned for Epic 4.

---

## Performance Considerations

### Performance Goals
*   **LCP:** < 2.5 seconds.
*   **Interaction Response:** < 100ms.
*   **Animation FPS:** 60 FPS.

---

## Next Steps

1.  **Begin High-Fidelity Design:** Create mockups and prototypes in Figma.
2.  **Handoff to Development:** This document is ready to guide frontend architecture and development.
