# TruthLens Project

This repository contains the source code for the TruthLens application.

## Local Development Setup

### Prerequisites
*   Node.js and npm
*   Python 3

### Instructions

1.  **Clone the repository.**
2.  **Install Frontend Dependencies:**
    ```bash
    cd truthlens-app/apps/web
    npm install
    ```
3.  **Install Backend Dependencies:**
    ```bash
    cd truthlens-app/apps/api
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
4.  **Run the Development Servers:**
    *   **Frontend:**
        ```bash
        cd truthlens-app/apps/web
        npm start
        ```
    *   **Backend:**
        ```bash
        cd truthlens-app/apps/api
        source venv/bin/activate
        uvicorn main:app --reload
        ```
