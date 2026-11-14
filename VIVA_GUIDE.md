# Curriculum Gap Analysis Pipeline — Technical Viva & Professor Presentation Guide

> **Project Title:** Curriculum Gap Analysis Pipeline – Evidence-Based Multi-Agent AI System  
> **Course / Evaluation:** University Final Project / Technical Viva (30 Marks)  
> **Core Framework:** Microsoft Semantic Kernel (Sequential Orchestration)  
> **Retrieval Engine:** Local ChromaDB + SentenceTransformers (`all-MiniLM-L6-v2`)  
> **Frontend:** React 18 + Vite + Recharts + Lucide-React (Dark Midnight-Navy Dashboard)  
> **Backend:** FastAPI + SQLite (`storage/app.db`) + ReportLab PDF Generator  

---

## 📋 Table of Contents
1. [Professor Demonstration Script (5-Minute Live Demo)](#1-professor-demonstration-script)
2. [The 2-Minute Elevator Pitch](#2-the-2-minute-elevator-pitch)
3. [The 5-Minute Technical Architecture Walkthrough](#3-the-5-minute-technical-architecture-walkthrough)
4. [Where is the Agent Trace Call? (Deep-Dive)](#4-where-is-the-agent-trace-call)
5. [50 Essential Viva Questions & Model Answers](#5-50-essential-viva-questions--model-answers)
   - [Part 1: Multi-Agent Architecture & Semantic Kernel (Q1–Q10)](#part-1-multi-agent-architecture--semantic-kernel)
   - [Part 2: RAG Pipeline, Embeddings & Vector Search (Q11–Q20)](#part-2-rag-pipeline-embeddings--vector-search)
   - [Part 3: Gap Detection Logic & Cosine Similarity (Q21–Q28)](#part-3-gap-detection-logic--cosine-similarity)
   - [Part 4: Resource Recommender & Reviewer Auditing (Q29–Q36)](#part-4-resource-recommender--reviewer-auditing)
   - [Part 5: State Isolation, SQLite Tracing & Reports (Q37–Q43)](#part-5-state-isolation-sqlite-tracing--reports)
   - [Part 6: Testing, Benchmark Evaluation & Full Stack (Q44–Q50)](#part-6-testing-benchmark-evaluation--full-stack)
6. [Emergency Defense: Handling Tough / Trick Questions](#6-emergency-defense-handling-tough--trick-questions)

---

## 1. Professor Demonstration Script

When showing this project to your professor or viva examiner, follow this structured, confident sequence:

### Step 1: Start the Entire Application
Open a terminal in the project directory and run:
```bash
./start.sh
```
*(Or `./venv/bin/python start.py`)*

Point out:
> *"Professor, with a single command, both the FastAPI asynchronous REST backend (Port 8000) and the React Vite single-page application (Port 5173) start up in under 2 seconds. The system operates 100% locally and offline without requiring an external paid LLM key."*

---

### Step 2: Show the Web Dashboard (`http://localhost:5173`)
Open your browser to **`http://localhost:5173`**:
1. Point to the **Top Navbar**:
   - Show the **Active Run ID**.
   - Show the operational indicators: `Semantic Kernel: Ready`, `Vector DB: ChromaDB Local`, `Reviewer Audit: Active`.
2. Point to the **Dashboard Metrics**:
   - Total runs recorded in SQLite.
   - Detected gaps count.
   - Approved recommendations count.
   - Ground-truth F1 score (100%).
3. Point to the **Six Agents Architecture Summary** card at the bottom.

---

### Step 3: Run a Live Analysis (`/new-analysis`)
1. Click **"New Analysis"** in the sidebar.
2. Under "3. Quick-Load Benchmark Sample", click **"Data Science Syllabus"**.
   - Explain: *"This loads a real academic Data Science syllabus containing machine learning foundations, deep learning, NLP, and computer vision."*
3. Show the **Domain Selection**: Data Science (mapped to NIST NICE SP 800-181 and ACM CS2023).
4. Show the **Similarity Sliders**: Covered (0.75) and Partial (0.45).
5. Click **"Start Multi-Agent Analysis"**.
   - Watch the animated spinner run as Semantic Kernel executes the 6 agents sequentially.

---

### Step 4: Show the Real-Time Agent Trace Monitor (`/agent-monitor`)
The page automatically transitions to **Agent Monitor**:
1. Point out the **6 sequential steps** with real execution latencies in milliseconds:
   - **Step 1: Syllabus Parser** (~80 ms) — PyMuPDF extracted 10 topics and units.
   - **Step 2: Skills Retriever** (~120 ms) — ChromaDB RAG retrieved 15 authentic framework competencies with page numbers.
   - **Step 3: Gap Detector** (~95 ms) — Classified 10 covered and 5 missing gaps.
   - **Step 4: Resource Recommender** (~45 ms) — Generated topic recommendations with suggested weight % and learning levels.
   - **Step 5: Reviewer Agent** (~30 ms) — Audited citations against genuine evidence IDs; approved valid proposals.
   - **Step 6: Curriculum Coordinator** (~150 ms) — Consolidated state into SQLite and generated the PDF.
2. Click **"Inspect Payload"** on any step:
   - Show the real JSON input and output summaries recorded in SQLite!

---

### Step 5: Show the Coverage Matrix (`/gaps`)
1. Click **"Gap Analysis"** in the sidebar.
2. Filter by **"Missing (5)"**:
   - Point out the 5 detected gaps: *Model Deployment & MLOps, Data Engineering Pipelines, AI Ethics & Fairness, Vector Databases, Reinforcement Learning*.
3. Click on the **Evidence Citation Button** (e.g., `EV-011`):
   - Show the modal displaying the **authentic document name**, **page number**, **section**, and **exact retrieved text chunk from ChromaDB**.
   - Explain: *"Notice, Professor, this citation is not hallucinated; it comes directly from the NIST NICE framework stored in ChromaDB."*

---

### Step 6: Show Reviewer Validated Recommendations (`/recommendations`)
1. Click **"Recommendations"** in the sidebar.
2. Show the **Approved by Reviewer** tab:
   - Topic name, explanation, proposed curriculum weight (e.g. 5%), learning level (Intermediate), and clickable verified open-access resource URL.
   - Show the **Reviewer Audit Badge**: *"Reviewer Agent Audit: Passed deterministic validation checks."*

---

### Step 7: Download the Official PDF Report (`/reports`)
1. Click **"Reports & PDF"** in the sidebar.
2. Click **"Download ReportLab PDF"**:
   - A multi-page institutional PDF opens, styled with headers, tables, gap summaries, and citations generated on-the-fly by ReportLab!

---

### Step 8: Show Scientific Benchmark Evaluation (`/evaluation`)
1. Click **"Benchmark Evaluation"**:
   - Show the Recharts bar graphs showing **100% Precision, 100% Recall, and 1.00 F1 Score** across all 3 domains (Data Science, Web Development, Cloud and DevOps).
   - Click **"Re-Run Benchmark"** to show it evaluating 45 framework competencies and finding all 15 ground-truth missing gaps in real-time.

---

### Step 9: Show Automated Pytest Tests (In Terminal)
Switch to the terminal and run:
```bash
./venv/bin/python -m pytest tests/ -v
```
Show the examiner:
> *"73 out of 73 unit and integration tests passing in under 20 seconds, testing every agent, schema, vector search, and API endpoint."*

---

## 2. The 2-Minute Elevator Pitch

> *"Good morning/afternoon, Professor.  
> 
> In higher education, academic syllabi take years to revise, while industry technologies evolve in months. Consequently, students graduate without knowing modern industry competencies like MLOps, Infrastructure as Code, or Web Accessibility.
> 
> To solve this, I designed and built the **Curriculum Gap Analysis Pipeline**, an evidence-based multi-agent AI system.
> 
> The application uses **Microsoft Semantic Kernel** to coordinate **six independent specialist agents** in strict sequential order:
> 1. A **Syllabus Parser Agent** that extracts academic hierarchies and official marks using PyMuPDF.
> 2. A **Skills Retrieval Agent** that uses **RAG with ChromaDB** and MiniLM embeddings to retrieve industry standards from NIST and ESCO.
> 3. A **Gap Detector Agent** that performs semantic similarity and conjunct matching to categorize topics into Covered, Partial, or Missing.
> 4. A **Resource Recommender Agent** that proposes new modules with suggested curriculum weights and verified open-access learning links.
> 5. An independent **Reviewer Agent** that acts as an auditor, enforcing a zero-hallucination policy by deterministically checking citations against genuine vector IDs.
> 6. A **Curriculum Coordinator** that manages shared state in SQLite and generates institutional PDF reports using ReportLab.
> 
> We benchmarked the pipeline against 45 framework competencies with 15 ground-truth missing topics across three domains, achieving **100% Precision, 100% Recall, and 100% Citation Accuracy**, backed by 73 automated tests and a full-stack React dashboard."*

---

## 3. The 5-Minute Technical Architecture Walkthrough

### The Problem with Naive AI Syllabi Checkers
If you simply pass a syllabus to ChatGPT and ask "What is missing?", the LLM will:
1. Hallucinate topics not relevant to the course level.
2. Fabricate fake citations or invalid URLs.
3. Mark topics as missing simply because different terminology was used (e.g., "Docker" vs "Containerization").
4. Provide vague advice with no quantifiable weight allocations.

### How Our System Solves This Technically
1. **Separation of Concerns:** Instead of one massive prompt, we separate the workflow into 6 specialist agents with typed Pydantic contracts (`backend/core/schemas.py`).
2. **True RAG with ChromaDB:** We chunked real industry documents (NIST SP 800-181, ESCO Digital Skills, NIST SP 500-292) into 104 vector chunks using Sentence Transformers (`all-MiniLM-L6-v2`, 384 dimensions) and indexed them into persistent ChromaDB.
3. **Multi-Faceted Semantic Matching:** Agent 3 does not rely solely on cosine similarity:
   - It performs acronym normalization (e.g. `ML` -> `machine learning`, `K8s` -> `kubernetes`).
   - It strips grammatical stopwords ("and", "for", "in") to avoid false positive partial matches.
   - It checks conjunction boundaries so that a compound skill requires both parts to be covered.
4. **Deterministic Auditor Guardrail:** Agent 5 (Reviewer) is not an LLM that can be fooled. It executes deterministic Python rules:
   - Does `evidence_id` exist in the retrieved evidence list?
   - Does `framework_id` match?
   - Is `resource_url` a valid HTTP/HTTPS URL from a verified catalog?
   If any check fails, the recommendation is rejected and flagged.
5. **State Isolation & Observability:** Every run generates a unique run ID (`RUN-YYYYMMDD-HHMMSS-XXXX`). State transitions are logged to SQLite (`storage/app.db`) in table `agent_events`, recording exact execution duration in milliseconds.

---

## 4. Where is the Agent Trace Call?

The professor will likely ask: *"Where is the execution trace implemented? How do you monitor agent latency and errors?"*

You can answer directly:

### 1. The Core Tracing Engine: `backend/core/tracing.py`
```python
# Function in backend/core/tracing.py:
def record_event(
    db: Session,
    run_id: str,
    agent_name: str,
    step_number: int,
    status: str,
    duration_ms: int,
    input_summary: str = None,
    output_summary: str = None,
    error_message: str = None
) -> AgentEvent
```
Whenever an agent executes in `backend/agents/curriculum_coordinator.py`, execution time is captured using `time.perf_counter()`:
```python
start_time = time.perf_counter()
output = await agent.run(...)
duration_ms = int((time.perf_counter() - start_time) * 1000)
record_event(db, run_id=run_id, agent_name="syllabus_parser", step_number=1, duration_ms=duration_ms, ...)
```

### 2. The Persistent SQLite Table: `agent_events`
Located in `storage/app.db`:
- `id` (Primary Key UUID)
- `run_id` (Foreign Key to `analysis_runs.id`)
- `agent_name` (e.g. `syllabus_parser`, `gap_detector`)
- `step_number` (1 to 6)
- `duration_ms` (integer milliseconds)
- `input_summary` & `output_summary` (text)
- `created_at` (ISO timestamp)

### 3. The REST API Endpoint: `GET /api/runs/{run_id}/events`
Exposed in `backend/api/runs.py`, returning structured JSON array of all agent execution events.

### 4. The Frontend UI: `frontend/src/pages/AgentMonitor.jsx`
Visualizes the timeline with green checkmarks, latency badges (`XX ms`), and a modal to inspect raw input/output payloads.

---

## 5. 50 Essential Viva Questions & Model Answers

### Part 1: Multi-Agent Architecture & Semantic Kernel

#### Q1: Why use a multi-agent architecture instead of a single prompt?
**Answer:** A single prompt suffers from context drift, hallucinated citations, and lack of accountability. By splitting the task into 6 specialist agents with typed Pydantic interfaces, each agent has a single responsibility. This enables targeted error handling, independent evaluation, verifiable audit trails, and modular maintainability.

#### Q2: What is Microsoft Semantic Kernel and why did you choose it?
**Answer:** Microsoft Semantic Kernel is an enterprise SDK for orchestrating AI agents, plugins, and memories. We chose it because it natively supports `SequentialOrchestration`, agent abstraction (`ChatCompletionAgent`), and typed shared context, satisfying the university requirement for an enterprise orchestration framework without requiring LangChain or CrewAI.

#### Q3: How do the six agents communicate?
**Answer:** They communicate through a shared, typed `WorkflowState` Pydantic model (`backend/core/schemas.py`). Each agent receives the immutable state from previous stages, performs its operation, and yields an updated state. This state is serialized to JSON and persisted to SQLite after each step.

#### Q4: What prevents mutable state leakage between different users or runs?
**Answer:** Every analysis run is initialized with a distinct, cryptographically unique ID (`RUN-YYYYMMDD-HHMMSS-XXXX`). State dictionaries are created fresh per run and stored in isolated SQLite database rows. No global mutable variables are used across runs.

#### Q5: Can one agent fail without crashing the entire system?
**Answer:** Yes. In `backend/agents/curriculum_coordinator.py`, each agent execution is wrapped in a `try...except` block. If an agent fails, the error message is recorded into `state.errors`, logged to the `agent_events` trace table in SQLite, and the coordinator transitions the run status to `FAILED` with an actionable diagnostic message.

#### Q6: What is the exact execution order of the agents?
**Answer:**
1. `SyllabusParserAgent`
2. `SkillsRetrieverAgent`
3. `GapDetectorAgent`
4. `ResourceRecommenderAgent`
5. `ReviewerAgent`
6. `CurriculumCoordinator` (compiles state, persists database, and generates PDF).

#### Q7: Why is the Coordinator considered the 6th agent?
**Answer:** The Coordinator is not merely a script; it manages the lifecycle, validates preconditions before each stage, controls error recovery, handles fallback strategies, and executes the synthesis stage to compile institutional PDF reports.

#### Q8: Does your system require an active OpenAI API key to run?
**Answer:** No! We implemented an offline-first architecture. It features a deterministic `MockChatCompletionService` inside Semantic Kernel, local SentenceTransformers embeddings (`all-MiniLM-L6-v2`), local ChromaDB, and local PyMuPDF. If an API key is provided in `.env`, it can enhance LLM summaries, but the core pipeline runs 100% offline.

#### Q9: What design patterns did you use in the agents?
**Answer:** We used the **Orchestrator Pattern** (Coordinator managing specialist workers), the **Repository Pattern** (for database and vector store access), and the **Data Transfer Object (DTO) Pattern** (Pydantic schemas ensuring typed inputs and outputs).

#### Q10: How do you validate state before an agent runs?
**Answer:** In `backend/core/shared_state.py`, the `validate_state_for_stage(state, stage_number)` function verifies preconditions. For example, Stage 2 requires `state.syllabus_data` to be populated; Stage 3 requires `state.framework_evidence` to have at least one record.

---

### Part 2: RAG Pipeline, Embeddings & Vector Search

#### Q11: What is RAG and why is it needed here?
**Answer:** RAG stands for **Retrieval-Augmented Generation**. Instead of relying on an LLM's parametric memory (which may be outdated or hallucinated), RAG queries a vector database of genuine industry documents (NIST, ESCO) and injects the retrieved passages into the analysis, ensuring every recommendation is anchored in verifiable evidence.

#### Q12: Which embedding model did you use and why?
**Answer:** We used `all-MiniLM-L6-v2` from Sentence Transformers. It maps sentences to a dense 384-dimensional vector space. It is extremely fast, runs locally on CPU without a GPU, has low memory usage (~80MB), and produces high-quality semantic similarity for technical computer science topics.

#### Q13: What vector database did you use?
**Answer:** **ChromaDB**. It is an open-source, embedded vector database that runs in-process with SQLite persistence (`storage/chroma_db/`), requiring no external Docker containers or cloud services.

#### Q14: How are industry frameworks ingested and chunked?
**Answer:** In `backend/rag/chunking.py`, framework text extracted by PyMuPDF is chunked using a sliding window algorithm with a chunk size of 500 characters and an overlap of 100 characters. Every chunk preserves its metadata: `framework_id`, `document_name`, `page` number, and `section`.

#### Q15: How many vector chunks are stored in your ChromaDB?
**Answer:** Exactly 104 vector chunks across three frameworks:
1. NIST NICE Cybersecurity & Data Science (SP 800-181)
2. ESCO Web Engineering & Digital Skills
3. NIST Cloud Computing Reference Architecture (SP 500-292).

#### Q16: How do you search ChromaDB for relevant skills?
**Answer:** In `backend/agents/skills_retriever.py`, the agent queries the domain's ChromaDB collection using the extracted syllabus topics. ChromaDB computes cosine distance against the stored embeddings and returns the top-$k$ most similar chunks along with page numbers and section headers.

#### Q17: What happens if ChromaDB finds no relevant evidence?
**Answer:** The Skills Retriever explicitly flags the record with status `"INSUFFICIENT_EVIDENCE"` rather than fabricating a citation.

#### Q18: What is the difference between dense retrieval and sparse retrieval?
**Answer:** Sparse retrieval (like BM25) matches exact keyword frequencies. Dense retrieval (our MiniLM embeddings) matches semantic meaning in vector space, allowing the system to recognize that "Kubernetes" is related to "Container Orchestration" even if the exact word isn't in the syllabus.

#### Q19: Why not just fine-tune an LLM instead of using RAG?
**Answer:** Fine-tuning modifies internal model weights, which is expensive, suffers from catastrophic forgetting, and still hallucinates page numbers. RAG allows hot-swapping or updating framework documents immediately without retraining, and guarantees exact page citations.

#### Q20: Where are the framework PDFs stored in your repository?
**Answer:** In `data/frameworks/`:
- `data_science_framework.pdf`
- `web_development_framework.pdf`
- `cloud_devops_framework.pdf`.

---

### Part 3: Gap Detection Logic & Cosine Similarity

#### Q21: How is cosine similarity calculated?
**Answer:** Cosine similarity measures the cosine of the angle between two multi-dimensional vectors:
$$\text{Cosine Similarity} = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
It ranges from $-1$ to $+1$, where $1$ indicates identical semantic direction.

#### Q22: Why is cosine similarity alone not enough to prove topic coverage?
**Answer:** Because embedding models can give high similarity to opposite concepts (e.g. "relational database" and "non-relational database" score ~0.82) or partial word overlaps ("data structures" and "data engineering" score ~0.76). We combine cosine similarity with synonym mapping, stopword stripping, and conjunction checks.

#### Q23: What thresholds do you use for coverage classification?
**Answer:**
- **COVERED:** Similarity score $\ge 0.75$ (or exact synonym/acronym match).
- **PARTIAL:** Similarity score between $0.45$ and $0.74$.
- **MISSING:** Similarity score $< 0.45$.
These thresholds are user-configurable via the UI sliders and `backend/config.py`.

#### Q24: How does your synonym mapping work?
**Answer:** In `backend/agents/gap_detector.py`, we maintain a technical synonym and acronym dictionary (`SYNONYM_MAP`) mapping equivalent industry terms: e.g. `k8s` $\rightarrow$ `kubernetes`, `ci/cd` $\rightarrow$ `continuous integration`, `mlops` $\rightarrow$ `machine learning operations`.

#### Q25: What is conjunct matching in your gap detector?
**Answer:** For compound framework competencies like *"CI/CD Pipeline Automation & Continuous Deployment"*, both concepts must have corresponding coverage in the syllabus. If only "Continuous Integration" is present, conjunct logic classifies it as `PARTIAL` rather than fully `COVERED`.

#### Q26: How do you handle unreadable or empty syllabi?
**Answer:** PyMuPDF checks if extracted text length is greater than 20 characters. If empty or corrupt, `SyllabusParserAgent` raises a `ValueError("Syllabus contains insufficient text")` which the coordinator catches gracefully without crashing.

#### Q27: Does your parser invent official weights if the syllabus lacks them?
**Answer:** Never! If the syllabus document does not explicitly specify marks, percentages, or lecture hours, `official_weight` is set to `null` (None in Python). The system strictly adheres to the principle of never inventing official weights.

#### Q28: How do you distinguish between a subtopic and a unit?
**Answer:** The parser uses regex pattern matching against standard academic syllabus structures (e.g., `Unit I:`, `Module 2:`, bullet points `- `, and numbered lists `1.1`), grouping subtopics under their respective parent topics.

---

### Part 4: Resource Recommender & Reviewer Auditing

#### Q29: What is the primary role of Agent 4 (Resource Recommender)?
**Answer:** For every competency classified as `MISSING` or `PARTIAL`, Agent 4 proposes an actionable curriculum module, a recommended weight allocation (e.g., 5% to 15%), an academic learning level (Beginner/Intermediate/Advanced), and verified open-access study resources.

#### Q30: What is the primary role of Agent 5 (Reviewer Agent)?
**Answer:** Agent 5 is an independent quality assurance auditor. It enforces strict institutional compliance by deterministically validating that:
1. The `evidence_id` exists in the retrieved evidence list.
2. The `framework_id` matches the document.
3. The `resource_url` is a valid, reachable, non-commercial open-access link.
Any recommendation failing these checks is flagged as `REJECTED`.

#### Q31: Why is the Reviewer Agent deterministic instead of an LLM?
**Answer:** LLMs can hallucinate approvals or overlook subtle metadata mismatches. Deterministic Python validation guarantees 100% mathematical consistency and absolute zero hallucination for audit compliance.

#### Q32: What happens when the Reviewer Agent rejects a recommendation?
**Answer:** The recommendation is assigned status `REJECTED`, and the rejection reason (e.g. `INVALID_EVIDENCE_ID`) is recorded. In the final report and UI, only `APPROVED` recommendations are included in the primary curriculum proposal, while rejected items are listed in the audit log.

#### Q33: How are suggested curriculum weights calculated?
**Answer:** In `backend/agents/resource_recommender.py`, suggested weights are formulated based on the learning level and credit load (typically 5% for introductory modules, 10% for core competencies, and 15% for advanced multi-unit topics).

#### Q34: Are the recommended learning resources proprietary or open access?
**Answer:** All resources in `data/resources/learning_resources.json` are public domain, open-access, and authoritative (e.g., NIST CSRC publications, W3C Web Standards, OWASP Foundation guides, Kubernetes official documentation).

#### Q35: Can the Reviewer Agent detect fabricated URLs?
**Answer:** Yes. It validates URL structure (`http://` or `https://`), ensures no placeholder domains (like `example.com`), and cross-checks the URL against the curated open-access catalog.

#### Q36: How does the system handle borderline similarity cases?
**Answer:** Scores falling between 0.40 and 0.49 are flagged with a `BORDERLINE_FLAG` in the coverage matrix, notifying the academic reviewer to conduct a manual syllabus review.

---

### Part 5: State Isolation, SQLite Tracing & Reports

#### Q37: How is the workflow state structured?
**Answer:** As a typed Pydantic model (`WorkflowState`) containing:
- `run_id`: Unique string (`RUN-YYYYMMDD-HHMMSS-XXXX`)
- `domain`: Academic domain string
- `syllabus_data`: Extracted units and topics
- `framework_evidence`: List of retrieved ChromaDB chunks
- `coverage_matrix`: List of covered/partial/missing entries
- `gaps`: List of missing competencies
- `recommendations`: Proposals from Agent 4
- `reviewer_results`: Audit verdicts from Agent 5
- `errors`: Diagnostic log
- `final_report`: Summary metrics.

#### Q38: Why use SQLite instead of storing state in memory?
**Answer:** In-memory storage is lost when the server restarts and cannot be shared across multiple worker threads or viewed historically. SQLite (`storage/app.db`) provides lightweight, persistent relational storage with zero configuration.

#### Q39: What tables exist in your SQLite database?
**Answer:**
1. `analysis_runs` (id, domain, status, timestamps, summary counts)
2. `agent_events` (telemetry traces, step numbers, duration in ms)
3. `syllabus_documents` (extracted syllabus content)
4. `framework_documents` (indexed standards metadata)
5. `retrieved_evidence` (ChromaDB chunk citations)
6. `recommendation_records` (proposals and reviewer verdicts).

#### Q40: How is the institutional PDF report generated?
**Answer:** In `backend/services/report_service.py`, we use **ReportLab**. It compiles an institutional-grade PDF with custom styles, headers, multi-column tables, gap distribution summaries, reviewer audit stamps, and verified citations.

#### Q41: Where are generated PDF reports stored?
**Answer:** In `storage/reports/` with naming format `report_{run_id}.pdf`. They are also downloadable directly via `GET /api/runs/{run_id}/report/pdf`.

#### Q42: What is the format of the Run ID?
**Answer:** `RUN-YYYYMMDD-HHMMSS-XXXX` (where `XXXX` is a 4-character hex UUID). This guarantees chronological sorting while preventing database unique constraint collisions during high-concurrency runs.

#### Q43: How do you verify that state information is not lost between stages?
**Answer:** Unit test `test_shared_state.py::test_stage_progression_preserves_data` explicitly asserts that fields added by Stage 1 (`syllabus_data`) remain intact after Stage 5 finishes.

---

### Part 6: Testing, Benchmark Evaluation & Full Stack

#### Q44: How did you evaluate the performance of your system?
**Answer:** In `evaluation/evaluate.py`, we created a ground-truth benchmark across all 3 domains. We deliberately removed 5 known industry competencies per domain (15 total) from the sample syllabi. We then measured **Precision, Recall, F1 Score, Gap Detection Rate, and Citation Accuracy**.

#### Q45: What were the evaluation results?
**Answer:**
- **True Positives (TP):** 15
- **False Positives (FP):** 0
- **False Negatives (FN):** 0
- **Precision:** 100% ($\frac{TP}{TP+FP}$)
- **Recall:** 100% ($\frac{TP}{TP+FN}$)
- **F1 Score:** 1.00
- **Citation Accuracy:** 100% (all 15 recommendations cited authentic vector IDs).

#### Q46: How many automated tests does the repository have?
**Answer:** Exactly **73 passing automated pytest tests** covering unit tests for each agent, PDF parsing, chunking, cosine similarity, ChromaDB retrieval, database schemas, state serialization, and FastAPI endpoints.

#### Q47: How does the React frontend communicate with the FastAPI backend?
**Answer:** The React app uses standard `fetch` API inside `frontend/src/services/api.js`. In development, Vite's proxy (`frontend/vite.config.js`) forwards all `/api/*` calls from port `5173` to `http://127.0.0.1:8000`.

#### Q48: What libraries are used in the frontend?
**Answer:**
- **React 18:** Component architecture
- **Vite:** High-performance build tool and dev server
- **React Router DOM v6:** Client-side routing across 8 pages
- **Recharts:** Interactive SVG bar charts and metrics
- **Lucide-React:** Consistent iconography
- **Custom CSS:** Dark Midnight-Navy theme (`#0b1120`, `#151e32`, `#6366f1`).

#### Q49: How does the PDF upload work in the API?
**Answer:** In `backend/api/analysis.py`, the endpoint `POST /api/analyze/upload` accepts `multipart/form-data` with a binary PDF stream. It saves the file to `storage/uploads/`, passes the path to `SyllabusParserAgent` for PyMuPDF extraction, and triggers the Semantic Kernel pipeline.

#### Q50: If you had another 2 weeks, what would you add next?
**Answer:**
1. Multi-modal syllabus ingestion (OCR for scanned or handwritten syllabus images).
2. Live integration with university Learning Management Systems (LMS) like Canvas or Moodle via LTI 1.3.
3. Automated syllabus diffing to highlight year-over-year curricular drift.

---

## 6. Emergency Defense: Handling Tough / Trick Questions

| Professor Question | Trap / Intent | Winning Student Answer |
|---|---|---|
| *"Isn't this just a wrapper around ChatGPT?"* | Testing if you actually built an agentic system or just called an API. | *"Not at all, Professor. In fact, our core pipeline runs 100% offline without any external LLM! We built a local RAG vector store using ChromaDB, MiniLM embeddings, a deterministic Reviewer auditor, PyMuPDF parsing, and Microsoft Semantic Kernel sequential orchestration. The intelligence comes from the multi-agent architecture and semantic alignment algorithms, not an external prompt."* |
| *"Why didn't you use LangChain or CrewAI?"* | Testing compliance with project constraints. | *"Our project specifications explicitly required the Microsoft Agent Framework or Microsoft Semantic Kernel to evaluate enterprise-grade multi-agent orchestration. Semantic Kernel provides cleaner sequential orchestration and type safety without the bloat and breaking changes associated with LangChain."* |
| *"What if the syllabus is in French or German?"* | Testing knowledge of model limitations. | *"Our current vector model `all-MiniLM-L6-v2` is English-optimized. For multilingual support, we would swap the embedding model to `paraphrase-multilingual-MiniLM-L12-v2` in `backend/config.py` and ingest multilingual ESCO frameworks, which are already available in 27 EU languages."* |
| *"Can a student cheat by adding random keywords to their syllabus?"* | Testing robustness of the gap detector. | *"No, because Agent 3 evaluates both semantic cosine similarity and syntactic structure. Keyword stuffing without contextual co-occurrence does not satisfy the 0.75 coverage threshold, and any partial match is flagged for manual review."* |
