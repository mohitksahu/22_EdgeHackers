# Pluto - Multimodal RAG System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Pluto** is an advanced Multimodal Retrieval-Augmented Generation (RAG) system that processes and reasons over text, images, audio, and PDF documents using state-of-the-art AI models.

---

## 🌟 Features

### Multimodal Document Processing
- 📄 **Text & PDFs**: Extract and chunk text from documents and PDFs
- 🖼️ **Images**: OCR extraction with visual embeddings (CLIP)
- 🎵 **Audio**: Transcription using Faster-Whisper (CTranslate2)
- 📊 **Structured Data**: Handle CSV, JSON, and XML files

### Advanced RAG Pipeline
- 🧠 **LLM Reasoning**: Powered by Llama 3.2 1B (GGUF) with GPU acceleration
- 🔍 **Semantic Search**: ChromaDB vector store with CLIP embeddings
- 📊 **Evidence Evaluation**: Confidence scoring and hallucination detection
- 🔗 **Conflict Detection**: Identify contradictory information
- 🚫 **Smart Refusal**: Refuse to answer when evidence is insufficient

### GPU-Accelerated Performance
- ⚡ **CUDA Support**: Full GPU offloading for embeddings and LLM
- 🚀 **C++ Engines**: llama-cpp-python, fastembed (ONNX), faster-whisper
- 💾 **Optimized Memory**: Efficient model loading and caching

### Modern Web Interface
- 🎨 **Interactive UI**: React with Framer Motion animations
- 🌌 **3D Visualizations**: Three.js powered effects
- 📱 **Responsive Design**: TailwindCSS for beautiful layouts
- 🔄 **Real-time Updates**: Live query results and feedback

---

## 🏗️ Architecture

```
Pluto/
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── ingestion/     # Document processors (PDF, image, audio, text)
│   │   ├── retrieval/     # Semantic search & query analysis
│   │   ├── reasoning/     # LLM reasoning & evidence evaluation
│   │   ├── embeddings/    # CLIP multimodal embeddings
│   │   ├── storage/       # ChromaDB vector store
│   │   └── utils/         # GPU checks, logging, validation
│   ├── scripts/           # Setup & maintenance scripts
│   └── data/              # Models, uploads, vector store
└── frontend/              # React Frontend
    ├── src/
    │   ├── components/    # UI components
    │   ├── pages/         # App pages
    │   ├── services/      # API integration
    │   └── styles/        # CSS & animations
    └── public/            # Static assets
```

---

## 🚀 Quick Start

### Prerequisites

**System Requirements:**
- Python 3.11+
- Node.js 18+
- CUDA-capable GPU (recommended for performance)
- 8GB+ RAM
- 10GB+ disk space

**Windows Dependencies:**
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) for image text extraction
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/) for C++ compilation

---

### Backend Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd 22_EdgeHackers/Pluto
```

2. **Create virtual environment:**
```bash
cd backend
python -m venv .venv311
.venv311\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
# Install PyTorch with CUDA support first
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install llama-cpp-python with CUDA
set CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python --force-reinstall --no-cache-dir

# Install remaining dependencies
pip install -r requirements.txt
```

4. **Download models:**
```bash
python scripts/setup_models.py
```

This downloads:
- Llama 3.2 1B Instruct (GGUF, Q4_K_M quantization)
- CLIP ViT-B-32 (ONNX format for embeddings)
- Whisper Base (CTranslate2 format)

5. **Configure environment:**
```bash
# Create .env file
cp .env.example .env

# Edit configuration (optional)
# Set paths, API keys, model parameters
```

6. **Run the backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs

---

### Frontend Setup

1. **Navigate to frontend:**
```bash
cd ../frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Run development server:**
```bash
npm run dev
```

Frontend: http://localhost:5173

---

## 📖 Usage

### 1. Ingest Documents

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/file" \
  -F "file=@document.pdf" \
  -F "scope_id=my_project"
```

**Supported formats:**
- Documents: `.pdf`, `.txt`, `.md`, `.docx`
- Images: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`
- Audio: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`
- Data: `.csv`, `.json`, `.xml`

### 2. Query the System

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is photosynthesis?",
    "scope_id": "my_project",
    "top_k": 5
  }'
```

**Via Web UI:**
1. Open http://localhost:5173
2. Upload documents
3. Enter your query
4. View results with confidence scores and citations

### 3. Manage Vector Store

**Clear all documents:**
```bash
python scripts/reset_vectorstore.py
```

**Clean orphaned files:**
```bash
python scripts/cleanup_vectorstore.py --clean
```

**Verify database:**
```bash
python scripts/verify_no_autowipe.py
```

---

## 🔧 Configuration

### Backend Configuration (`backend/app/config.py`)

```python
# API Settings
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# Model Settings
LLAMA_MODEL_PATH = "data/models/llama-3.2-1b-instruct-q4_k_m.gguf"
CLIP_MODEL_NAME = "Qdrant/clip-ViT-B-32-text"
WHISPER_MODEL = "base"

# GPU Settings
LLAMA_CPP_N_GPU_LAYERS = 16  # Offload all layers to GPU
LLAMA_CPP_N_CTX = 4096       # Context window

# ChromaDB Settings
CHROMADB_DIR = "data/vectorstore/chromadb"
COLLECTION_NAME = "pluto_rag_v1"

# Retrieval Settings
SIMILARITY_THRESHOLD = 0.5
RERANKING_ENABLED = True
```

### Frontend Configuration (`frontend/src/config.js`)

```javascript
export const API_BASE_URL = 'http://localhost:8000/api/v1';
export const WS_URL = 'ws://localhost:8000/ws';
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test suite
pytest scripts/tests/unit/test_chunking.py
pytest scripts/tests/integration/test_ingestion_pipeline.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Test API connection
npm run test:connection

# Run linter
npm run lint
```

### ACID Test (Multimodal Alignment)

```bash
cd backend
python scripts/acid_test.py
```

This test verifies that multimodal embeddings (image + text) are properly aligned in the vector space.

---

## 🛠️ Development

### Project Structure

**Backend Modules:**
- `api/` - REST endpoints (ingest, query, vector operations)
- `ingestion/` - File processors and chunking strategies
- `retrieval/` - Query analysis, semantic search, reranking
- `reasoning/` - LLM generation, evidence evaluation, refusal engine
- `embeddings/` - Multimodal embeddings (CLIP text + vision)
- `storage/` - ChromaDB client and vector operations
- `utils/` - GPU checks, logging, topic normalization

**Key Features:**
- **Scope Isolation**: Each document set has a unique `scope_id` to prevent cross-contamination
- **Evidence Grounding**: LLM responses must be backed by retrieved evidence
- **Hallucination Prevention**: Automatic refusal when confidence < threshold
- **Multimodal Chunking**: Smart splitting for embeddings (235 chars for CLIP)

### Adding New Document Types

1. Create processor in `app/ingestion/processors/`:
```python
class MyProcessor:
    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.myext']
    
    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        # Your extraction logic
        return {'content': text, 'metadata': {...}}
```

2. Register in `ingestion_service.py`

---

## 🐛 Troubleshooting

### GPU Not Detected

**Check CUDA installation:**
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

**Reinstall llama-cpp-python with CUDA:**
```bash
set CMAKE_ARGS="-DGGML_CUDA=on"
pip uninstall llama-cpp-python
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### "Module not found" errors

```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### ChromaDB permission errors

```bash
# Reset vector store
python scripts/reset_vectorstore.py
```

### Tesseract OCR not found (Windows)

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH or set in `.env`:
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## 📊 Performance Optimization

### GPU Memory Management

```python
# Reduce context window for lower VRAM
LLAMA_CPP_N_CTX = 2048  # Instead of 4096

# Reduce batch size
LLAMA_CPP_N_BATCH = 256  # Instead of 512

# Offload fewer layers
LLAMA_CPP_N_GPU_LAYERS = 8  # Instead of 16
```

### Caching

- Models are cached on first load (singleton pattern)
- Embeddings are generated once per chunk
- Vector store uses HNSW index for fast retrieval

### Scaling

- Deploy with Gunicorn for multi-worker support
- Use Redis for distributed caching
- Consider Pinecone/Weaviate for cloud vector storage

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

**Code Style:**
- Python: Follow PEP 8, use type hints
- JavaScript: ESLint configuration provided
- Write tests for new features
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

**Models & Libraries:**
- [Meta Llama](https://github.com/meta-llama/llama) - Language model
- [OpenAI CLIP](https://github.com/openai/CLIP) - Multimodal embeddings
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - Audio transcription
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://reactjs.org/) - Frontend framework

**Special Thanks:**
- EdgeHackers Team - Project development
- Open source community for amazing tools

---

## 📞 Support

For issues and questions:
- 🐛 [GitHub Issues](https://github.com/yourusername/22_EdgeHackers/issues)
- 📧 Email: support@yourproject.com
- 💬 Discord: [Join our community](https://discord.gg/yourserver)

---

## 🗺️ Roadmap

- [ ] **v1.1** - Add video processing support
- [ ] **v1.2** - Multi-language support for queries
- [ ] **v1.3** - Fine-tuning interface for custom domains
- [ ] **v2.0** - Multi-user authentication and collaboration
- [ ] **v2.1** - Cloud deployment templates (AWS, Azure, GCP)
- [ ] **v3.0** - Agentic workflows and tool use

---

**Built with ❤️ by the EdgeHackers Team**

*"Making AI accessible, one query at a time."*
