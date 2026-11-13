# Curriculum Gap Analysis Pipeline

An intelligent, evidence-based Multi-Agent AI application designed to bridge the gap between academic curricula and evolving industry skill requirements.

The system uses a coordinated team of specialised AI agents to parse academic syllabi, retrieve relevant industry competencies using Retrieval-Augmented Generation (RAG), identify missing and partially covered skills, and recommend curriculum improvements with verifiable framework citations.

### Key Features
- **Multi-Agent Architecture:** Six specialised agents working together through sequential orchestration.
- **Syllabus Analysis:** Extracts subjects, units, topics and weights from PDF documents or pasted text.
- **RAG-Based Retrieval:** Uses ChromaDB and Sentence Transformers to retrieve relevant industry framework evidence.
- **Intelligent Gap Detection:** Classifies competencies as Covered, Partially Covered or Missing.
- **Resource Recommendations:** Suggests additional topics, recommended curriculum weights and learning resources.
- **Citation Validation:** A dedicated Reviewer Agent verifies evidence and rejects unsupported recommendations.
- **Shared Memory:** Maintains structured workflow state across agent executions.
- **Agent Observability:** Records execution traces, processing times, outputs and errors.
- **Evaluation Pipeline:** Measures precision, recall, F1-score, gap detection rate and citation coverage.
- **Interactive Dashboard:** Provides analysis reports, coverage matrices, agent monitoring and historical runs.

### Technology Stack
Python | Microsoft Agent Framework / Semantic Kernel | FastAPI | React | ChromaDB | Sentence Transformers | Pydantic | SQLAlchemy | SQLite | Docker

### Objective
To help educational institutions identify curriculum deficiencies and make evidence-based improvements aligned with industry competency frameworks.