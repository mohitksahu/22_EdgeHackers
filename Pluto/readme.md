# 🪐 Pluto - Multimodal RAG System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18.2+-61DAFB?logo=react" alt="React">
  <img src="https://img.shields.io/badge/LangGraph-0.0.40+-orange" alt="LangGraph">
  <img src="https://img.shields.io/badge/Qdrant-Vector%20DB-red" alt="Qdrant">
  <img src="https://img.shields.io/badge/Version-2.0.0-purple" alt="Version">
</p>

A robust **Multimodal Retrieval-Augmented Generation (RAG)** system designed to ingest, store, retrieve, and generate responses from heterogeneous real-world data sources including text documents (PDF, DOC, TXT), images (scans, diagrams, photographs), and audio recordings.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔄 **Multimodal Ingestion** | Process text, images, and audio with modality-specific pipelines |
| 🧠 **Unified Embeddings** | CLIP-based embeddings for cross-modal semantic alignment |
| 🎯 **Intent-Aware Retrieval** | Dynamic modality selection based on query analysis |
| 📊 **Evidence Grounding** | Responses strictly grounded in retrieved evidence |
| ⚡ **GPU Acceleration** | Optimized for NVIDIA RTX GPUs (tested on RTX 3050 6GB) |
| 🔍 **Hybrid Search** | BM25 + vector search with MMR reranking |
| 🤖 **LangGraph Orchestration** | Multi-agent workflow for complex reasoning |
| 🛡️ **Hallucination Prevention** | Refusal logic when evidence is insufficient |
| 💬 **Chat History** | Persistent session-based conversation management |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              PLUTO SYSTEM                               │
├─────────────────┬─────────────────────────────┬─────────────────────────┤
│    Frontend     │         Backend             │       Data Layer        │
│    (React)      │        (FastAPI)            │                         │
├─────────────────┼─────────────────────────────┼─────────────────────────┤
│                 │                             │                         │
│  • Dashboard    │  ┌─────────────────────┐    │   ┌─────────────────┐   │
│  • File Upload  │  │   LangGraph Agent   │    │   │     Qdrant      │   │
│  • Chat UI      │  │   ┌───────────────┐ │    │   │   Vector DB     │   │
│  • Sessions     │  │   │Query Analysis │ │◄───┼──►│                 │   │
│                 │  │   └───────────────┘ │    │   │  • Embeddings   │   │
│  React 18       │  │   ┌───────────────┐ │    │   │  • Metadata     │   │
│  Tailwind CSS   │  │   │  Retrieval    │ │    │   │  • Documents    │   │
│  Framer Motion  │  │   └───────────────┘ │    │   └─────────────────┘   │
│  Three.js       │  │   ┌───────────────┐ │    │                         │
│                 │  │   │  Generation   │ │    │   ┌─────────────────┐   │
│                 │  │   └───────────────┘ │    │   │     Ollama      │   │
│                 │  └─────────────────────┘    │   │   (LLM Server)  │   │
│                 │                             │   │                 │   │
│                 │  ┌─────────────────────┐    │   │  • Llama 3.2    │   │
│                 │  │   Ingestion Engine  │    │   │  • Mistral      │   │
│                 │  │   • PDF Processor   │    │   └─────────────────┘   │
│                 │  │   • Image OCR       │    │                         │
│                 │  │   • Audio Whisper   │    │                         │
│                 │  └─────────────────────┘    │                         │
└─────────────────┴─────────────────────────────┴─────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **NVIDIA GPU** with CUDA 12.1+ (optional but recommended)
- **Ollama** for LLM inference
- **Docker & Docker Compose** (for containerized deployment)

### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/droit8/Pluto.git
cd Pluto

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:80
# Backend API: http://localhost:8000
# Qdrant Dashboard: http://localhost:6333/dashboard
```

### Option 2: Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start Qdrant (required)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:5173
```

#### 3. Ollama Setup

```bash
# Install Ollama (https://ollama.ai)
# Then pull the model
ollama pull llama3.2:1b

# Verify it's running
ollama list
```

---

## 📁 Project Structure

```
Pluto/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   │   └── endpoints/     # ingest, query, session, vector
│   │   ├── graph/             # LangGraph workflow
│   │   │   ├── nodes/         # Graph nodes (retrieval, generation, etc.)
│   │   │   └── agents/        # Multi-agent architecture
│   │   ├── ingestion/         # Document processing
│   │   │   └── processors/    # PDF, image, audio processors
│   │   ├── retrieval/         # Search & retrieval
│   │   │   └── retrievers/    # BM25, hybrid, MMR
│   │   ├── reasoning/         # LLM reasoning
│   │   │   └── llm/           # Ollama integration
│   │   ├── embeddings/        # CLIP embeddings
│   │   └── storage/           # Vector store (Qdrant)
│   ├── scripts/               # Utility scripts
│   └── requirements.txt
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API clients
│   │   └── styles/            # Tailwind styles
│   └── package.json
│
├── config/                     # Configuration files
│   ├── backend.yaml
│   ├── frontend.yaml
│   └── models.yaml
│
├── data/                       # Data directories
│   ├── uploads/               # Uploaded files
│   ├── vectorstore/           # Qdrant persistence
│   └── models/                # ML models
│
└── docker-compose.yml         # Docker orchestration
```

---

## 🔌 API Endpoints

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/upload` | Upload and process files |
| `GET` | `/api/v1/ingest/status/{job_id}` | Check ingestion status |
| `DELETE` | `/api/v1/ingest/{doc_id}` | Delete a document |

### Query

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Submit a query |
| `POST` | `/api/v1/query/stream` | Stream query response |
| `GET` | `/api/v1/query/history` | Get query history |

### Session

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/session/create` | Create a new session |
| `GET` | `/api/v1/session/{id}` | Get session details |
| `DELETE` | `/api/v1/session/{id}` | Delete a session |

### Vector Store

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/vector/info` | Get collection info |
| `GET` | `/api/v1/vector/search` | Direct vector search |
| `DELETE` | `/api/v1/vector/reset` | Reset vector store |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `localhost` | Qdrant server host |
| `QDRANT_PORT` | `6333` | Qdrant server port |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:1b` | LLM model to use |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEBUG` | `true` | Debug mode |

### GPU / VRAM Configuration

The system is optimized for RTX 3050 6GB but scales to other GPUs:

```
VRAM Allocation (6GB):
├── Ollama LLM (1B): ~1.5GB
├── CLIP Embeddings: ~0.8GB
├── Whisper (base):  ~0.5GB
├── Qdrant/Other:    ~0.5GB
└── Buffer:          ~0.5GB
    Total: ~3.8GB
```

---

## 🔄 LangGraph Workflow

```
┌──────────────┐
│ Query Input  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Query Analysis│ ◄─── Intent detection, modality routing
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Compat. Gate │ ◄─── Topic-concept compatibility check
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Retrieval   │ ◄─── Hybrid search (BM25 + Vector + MMR)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Evidence Grade│ ◄─── GPU-accelerated relevance scoring
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Conflict    │ ◄─── Detect contradictory evidence
│  Detection   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Generation  │ OR  │   Refusal    │ ◄─── If evidence insufficient
└──────────────┘     └──────────────┘
```

---

## 📊 ML Models

| Component | Model | Purpose |
|-----------|-------|---------|
| **Embeddings** | CLIP ViT-B/32 | Multimodal embeddings |
| **Transcription** | Whisper Base | Audio-to-text |
| **LLM** | Llama 3.2 1B (via Ollama) | Response generation |
| **Reranking** | Cross-Encoder | Result reranking |
| **BM25** | rank-bm25 | Sparse retrieval |

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `pluto-frontend` | 80 | React frontend (Nginx) |
| `pluto-backend` | 8000 | FastAPI backend |
| `pluto-qdrant` | 6333, 6334 | Qdrant vector database |

---

## 🧪 Running Tests

```bash
cd backend

# Test ingestion pipeline
python scripts/test_ingestion.py

# Test chat history
python scripts/test_chat_history.py

# Test Ollama connection
python scripts/test_ollama.py

# Benchmark performance
python scripts/benchmark_performance.py

# Check Ollama GPU usage
python scripts/check_ollama_gpu.py
```

---

## 📈 Performance

### GPU Acceleration Benefits

| Component | CPU | GPU | Speedup |
|-----------|-----|-----|---------|
| CLIP Embeddings | ~500ms | ~50ms | **10x** |
| Whisper Transcription | ~30s/min | ~6s/min | **5x** |
| Vector Search (Qdrant) | ~10ms | ~10ms | N/A |

### Recommended Hardware

- **Minimum**: 8GB RAM, 4-core CPU
- **Recommended**: 16GB RAM, RTX 3050+ (6GB VRAM)
- **Optimal**: 32GB RAM, RTX 3080+ (10GB+ VRAM)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

<p align="center">
  Built with ❤️ using FastAPI, React, LangGraph, and Qdrant
</p>