# Project Brief: TruthLens

### **Executive Summary**

TruthLens is a news summarization app that uses Retrieval-Augmented Generation (RAG) and blockchain verification to deliver bias-aware, fact-checked summaries. It aims to solve the problem of media bias and information overload by providing users with a transparent, interactive tool to explore different perspectives of a news story. The target market is discerning news consumers who are skeptical of single sources and seek a verifiable, multi-faceted understanding of events. The key value proposition is to empower users to see the full picture, verify claims, and understand the spectrum of bias in news reporting.

---

### **Problem Statement**

In the modern digital landscape, news consumers face a deluge of information from sources with opaque biases, making it difficult to form a balanced and accurate understanding of events. The primary pain points are:

*   **Information Overload:** The sheer volume of news from countless sources is overwhelming, making manual cross-referencing and verification an impractical task for the average person.
*   **Hidden Bias:** Most news sources present information through a specific lens, but this bias is rarely acknowledged, leaving readers to navigate complex narratives without a clear map of the landscape.
*   **Lack of Integrated Verification:** While fact-checking organizations exist, their services are disconnected from the daily news consumption experience. Readers cannot easily and instantly verify claims within the context of the article they are reading.

Existing solutions like news aggregators group articles but do not synthesize them or analyze their bias. This leaves the cognitive burden on the user. The impact is a decline in media trust and an increase in societal polarization. This environment creates a fertile ground for misinformation and 'fake news' to spread unchecked, making a tool that empowers users to independently verify facts a critical line of defense.

---

### **Proposed Solution**

TruthLens is a modular, agent-based platform designed to provide users with a transparent and interactive way to consume news. The core of the solution is a multi-agent system that automates the process of retrieving, verifying, summarizing, and analyzing news content from a wide array of sources.

Our key differentiators are:
1.  **Integrated Blockchain Verification:** Unlike any existing news aggregator, TruthLens will verify the authenticity of news articles by checking their hashes against records on a public blockchain, providing a tamper-proof "proof of origin."
2.  **Interactive Bias & Format Exploration:** TruthLens goes beyond static summaries. Users can dynamically explore the bias of the underlying sources using topic-specific sliders (e.g., political, industrial) and can choose to view the summary in multiple formats, including a "Debate Format" and a visual "Venn Diagram," to better understand different perspectives.
3.  **Agentic Architecture:** The system is built as a collection of specialized, independent agents (e.g., Retrieval, Verification, Summarization). This modularity allows for rapid evolution, enabling us to swap in better LLMs, different blockchain technologies, or new analysis modules without rebuilding the entire system.

This approach will succeed by empowering users directly within their news consumption workflow, replacing the current high-friction process of manual verification and cross-referencing with a seamless, engaging, and deeply informative experience. The long-term vision is for TruthLens to become the trusted lens through which anyone can gain a verifiable and holistic understanding of the world.

---

### **Target Users**

#### **Primary User Segment: "The Skeptical Verifier"**

*   **Profile:** Tech-savvy news consumers (ages 25-55) who are active on platforms where news is debated (e.g., Reddit, Twitter, Hacker News). They are disillusioned with the lack of transparency in mainstream media and have a strong desire for evidence-based reporting.
*   **Current Behaviors:** They currently spend a significant amount of time manually cross-referencing articles, researching sources, and reading comment sections to find alternative viewpoints. Their process is inefficient and labor-intensive.
*   **Needs & Pain Points:** They need a tool that drastically speeds up their verification process. They are frustrated by paywalls, hidden biases, and the sheer effort required to feel truly informed. They distrust "black box" solutions and crave transparency.
*   **Goals:** To quickly get a comprehensive, verifiable, and multi-perspective view of a topic, allowing them to form their own informed opinions with confidence and efficiency.

---

### **Goals & Success Metrics**

#### **Business Objectives**
*   **Validate the Core Concept:** Achieve a weekly user retention rate of 20% within the first 3 months, demonstrating that users find ongoing value.
*   **Build an Early Adopter Base:** Reach 1,000 Monthly Active Users (MAU) by the end of the first quarter post-launch.

#### **User Success Metrics**
*   **Engagement:** A high interaction rate with core features, with at least 50% of users trying the Bias Slider or alternate summary formats.
*   **Verification:** A measurable number of clicks on the blockchain "Verify" links, indicating users value this feature.
*   **Perceived Value:** Positive qualitative feedback from user surveys, with users reporting that they feel more informed and trust the app's output.

#### **Key Performance Indicators (KPIs)**
*   Daily/Monthly Active Users (DAU/MAU)
*   Week 1 and Week 4 User Retention Rate
*   Number of Summaries Generated Per User
*   Feature Adoption Rate (% of users who use sliders, Venn diagrams, etc.)

---

### **MVP Scope**

#### **Core Features (Must-Haves for MVP)**
*   **Text & URL Query Input:** Users can start an inquiry by typing a topic or pasting an article URL.
*   **Expanded RAG Retrieval:** The system will retrieve information from news APIs, academic journals, government publications, and public datasets.
*   **Dual Summary Formats:** The AI will generate summaries in both a "Debate Format" and a visual "Venn Diagram Format."
*   **Topic-Specific Bias Sliders:** The UI will feature interactive, explained sliders for exploring different angles of bias relevant to the story.
*   **Blockchain Verification:** The system will perform "proof of origin" checks for sources against a public blockchain.
*   **Basic Highlighting:** The initial version will highlight `Fact ✅`, `Opinion ⚠️`, and `Contradiction ❌`.

#### **Out of Scope for MVP**
*   Voice Queries and Image (OCR) Inputs.
*   Advanced Highlighting categories like "Future Prediction" or "Attribution."
*   All Phase 2+ features from the original concept, including the interactive timeline, chatbot, gamification, and community/token features.

#### **MVP Success Criteria**
The MVP will be successful if it achieves the user adoption and retention goals we defined earlier. Success means proving that "Skeptical Verifiers" actively use and return to the platform for its unique verification and bias-exploration capabilities.

---

### **Post-MVP Vision**

#### **Phase 2 Features**
Following a successful MVP, the focus will shift to deepening user engagement and expanding input methods. Key features will include:
*   **Voice Queries** and advanced highlighting for "Future Predictions" and "Attribution."
*   An **Interactive Timeline** to visualize how a story evolves over time.
*   An **"Ask-the-News" Chatbot** for conversational exploration of topics.
*   **Gamified Trust Scores** to engage users in predicting headline accuracy.

#### **Long-term Vision (Moonshots)**
The long-term goal is to build a comprehensive, decentralized ecosystem for truth. This includes:
*   **Image Capture (OCR)** for analyzing physical media.
*   Developing a **community of users and publishers** with a reputation layer and tokenized incentives for high-quality fact-checking and curation.
*   Ultimately, positioning TruthLens as the foundational layer for verifiable information on the internet.

#### **Expansion Opportunities**
*   **Browser Extension:** A browser plugin that brings TruthLens's analysis directly to any article the user is reading anywhere on the web.
*   **API Access:** Offering a public API for third-party researchers and platforms to leverage our verification and analysis capabilities.
*   **New Content Verticals:** Expanding beyond news to analyze other content types, such as scientific papers, financial reports, or political speeches.

---

### **Technical Considerations**

#### **Platform Requirements**
*   **Target Platforms:** The primary platform will be a web application. A lightweight Telegram bot is a potential secondary interface.
*   **Browser Support:** Modern evergreen browsers (Chrome, Firefox, Safari, Edge).
*   **Performance Requirements:** MVP summaries should be generated in under 30 seconds.

#### **Technology Preferences**
*   **Frontend:** React.js using Tailwind CSS and shadcn/ui for components.
*   **Backend API:** FastAPI (Python)
*   **LLM/RAG:** LangChain with Claude or a local Ollama model.
*   **Vector DB:** Qdrant or Weaviate.
*   **Blockchain:** Polygon or an Ethereum Testnet.
*   **Decentralized Storage:** IPFS or Arweave.
*   **Database:** PostgreSQL (provided via Supabase).
*   **Hosting:** Vercel for the frontend and Supabase for the backend and database, utilizing their free tiers as a constraint.

#### **Architecture Considerations**
*   **Service Architecture:** A modular, agent-based system as described in the initial brief (UI Agent, Orchestrator Agent, Retrieval Agent, etc.). This allows for independent development and future scaling into microservices.
*   **Integration Requirements:** Must integrate with various third-party news APIs, blockchain nodes (e.g., via Infura or Alchemy), and the selected vector database.
*   **Security:** Standard web security best practices. Smart contracts for the verification agent must undergo security audits before any mainnet deployment.

---

### **Constraints & Assumptions**

#### **Constraints**
*   **Budget:** Zero. This project will be developed using only free and open-source tools.
*   **Hosting:** The project is constrained to the free tiers of Vercel and Supabase. This will impact scalability and resource availability.
*   **Timeline:** The initial roadmap is aggressive, aiming for a feature-rich MVP within approximately 6-8 weeks.
*   **Resources:** The project will be developed by a very small team, likely a solo developer.

#### **Key Assumptions**
*   **Source Availability:** We assume that a sufficient number of high-quality, diverse news sources are accessible via free APIs or decentralized storage.
*   **LLM Capability:** We assume the chosen LLMs (Claude/Ollama) are powerful enough to handle the complex summarization, analysis, and formatting tasks required for the MVP.
*   **Verification Viability:** We assume that hashing articles on a blockchain is a technically and practically viable method for verifying content origin.
*   **User Interest:** We assume there is a reachable audience of "Skeptical Verifiers" who will be interested in and actively use a tool like TruthLens.

---

### **Risks & Open Questions**

#### **Key Risks**
*   **Source Reliability:** The reliance on free news APIs is a significant risk. These APIs may be unreliable, have strict rate limits, or provide a limited selection of sources, which could compromise the quality and diversity of the summaries.
*   **LLM Performance:** The chosen LLMs might not be capable of consistently delivering the high-quality, nuanced summarization and analysis (Debate Format, Venn Diagrams, bias detection) that the product promises.
*   **Scalability of Free Tiers:** If the app becomes popular, it will likely exceed the usage limits of the Vercel and Supabase free tiers, potentially leading to downtime or forcing an unplanned migration.
*   **Blockchain Adoption:** The core verification feature is dependent on publishers adopting an on-chain hashing standard. If this doesn't happen, the feature may have limited utility.

#### **Open Questions**
*   What is the strategy for handling sources in different languages?
*   How can we design the "Bias Explorer" to prevent users from simply reinforcing their own biases (i.e., creating a more sophisticated filter bubble)?
*   What are the legal and ethical implications of scraping, summarizing, and analyzing content from sources with varied terms of service?

#### **Areas Needing Further Research**
*   A comprehensive survey of available free news APIs to assess their long-term viability.
*   Benchmarking Claude vs. local Ollama models specifically for the summarization and analysis tasks required.
*   Investigating existing standards or projects for on-chain content verification.
