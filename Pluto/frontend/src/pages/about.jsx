import { Link } from "react-router-dom";
import { useEffect } from "react";
import ThemeToggle from "../components/common/ThemeToggle";
import SplashCursor from "../components/SplashCursor";
import "../styles/Home.css";
import "../styles/components/about.css";

const About = () => {
  useEffect(() => {
    // Scroll to top when component mounts
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="about-page">
      {/* Hero */}
      <section className="about-hero">
        <h1 className="about-title">
          About <span>PLUTO.</span>
        </h1>
        <p className="about-subtitle">Retrieval-Augmented Generation for Evidence-Based Intelligence</p>
      </section>

      {/* What is RAG */}
      <section className="about-section">
        <h2>What is Retrieval-Augmented Generation?</h2>
        <p className="about-text">
          <strong>Retrieval-Augmented Generation (RAG)</strong> is an AI architecture that combines the power of
          large language models with external knowledge retrieval. Unlike traditional chatbots that rely solely on
          pre-trained knowledge, RAG systems can access and incorporate information from external sources in real-time,
          providing more accurate, up-to-date, and verifiable responses.
        </p>
      </section>

      {/* PLUTO Overview */}
      <section className="about-section">
        <h2>Introducing PLUTO</h2>
        <p className="about-text">
          <strong>PLUTO</strong> is a sophisticated RAG implementation designed specifically for evidence-driven
          intelligence. Built with a modular architecture, PLUTO processes multiple data modalities, maintains
          knowledge graphs, and provides transparent, source-attributed responses. Our system prioritizes
          correctness over confidence, making uncertainty and conflicts explicit rather than hiding them.
        </p>
      </section>

      {/* Core Architecture */}
      <section className="about-section">
        <h2>Core Architecture</h2>
        <div className="architecture-grid">
          <div className="arch-component">
            <h3>📥 Data Ingestion</h3>
            <p>Processes documents, images, audio, and structured data with intelligent chunking and metadata extraction.</p>
          </div>
          <div className="arch-component">
            <h3>🧠 Embeddings</h3>
            <p>Transforms multimodal content into vector representations using advanced embedding models.</p>
          </div>
          <div className="arch-component">
            <h3>📊 Vector Storage</h3>
            <p>High-performance vector databases (ChromaDB) for efficient similarity search and retrieval.</p>
          </div>
          <div className="arch-component">
            <h3>🔗 Knowledge Graph</h3>
            <p>Builds semantic relationships between concepts, entities, and documents for enhanced reasoning.</p>
          </div>
          <div className="arch-component">
            <h3>🎯 Retrieval</h3>
            <p>Multi-strategy retrieval combining semantic search, graph traversal, and reranking algorithms.</p>
          </div>
          <div className="arch-component">
            <h3>🤔 Reasoning Engine</h3>
            <p>Advanced reasoning capabilities including conflict detection, uncertainty quantification, and hallucination prevention.</p>
          </div>
        </div>
      </section>

      {/* Data Types Supported */}
      <section className="about-section">
        <h2>Supported Data Modalities</h2>
        <div className="data-types">
          <div className="data-type">
            <h4>📄 Documents</h4>
            <p>PDF, DOCX, TXT, Markdown, LaTeX, and other text formats with layout preservation</p>
          </div>
          <div className="data-type">
            <h4>🖼️ Images</h4>
            <p>JPEG, PNG, WebP with OCR capabilities and visual content understanding</p>
          </div>
          <div className="data-type">
            <h4>🎵 Audio</h4>
            <p>MP3, WAV, M4A with speech-to-text transcription and speaker identification</p>
          </div>
          <div className="data-type">
            <h4>📊 Structured Data</h4>
            <p>JSON, CSV, XML, databases with schema-aware processing</p>
          </div>
          <div className="data-type">
            <h4>🌐 Web Content</h4>
            <p>URLs, APIs, and web scraping with content validation</p>
          </div>
          <div className="data-type">
            <h4>🔗 Code & APIs</h4>
            <p>Source code, API documentation, and technical specifications</p>
          </div>
        </div>
      </section>

      {/* Evidence-Based Reasoning */}
      <section className="about-section">
        <h2>Evidence-Based Reasoning</h2>
        <p className="about-text">
          PLUTO's reasoning engine goes beyond simple question-answering. It provides:
        </p>
        <ul className="reasoning-features">
          <li><strong>Source Attribution:</strong> Every claim is linked to specific sources with page numbers, timestamps, or coordinates</li>
          <li><strong>Confidence Scoring:</strong> Quantitative uncertainty estimates for each piece of information</li>
          <li><strong>Conflict Detection:</strong> Identifies when sources provide contradictory information</li>
          <li><strong>Hallucination Prevention:</strong> Cross-references generated content against source material</li>
          <li><strong>Multi-Perspective Analysis:</strong> Presents different viewpoints when sources disagree</li>
        </ul>
      </section>

      {/* Technical Specifications */}
      <section className="about-section">
        <h2>Technical Specifications</h2>
        <div className="specs-grid">
          <div className="spec-item">
            <h4>Backend Framework</h4>
            <p>FastAPI with async processing and RESTful APIs</p>
          </div>
          <div className="spec-item">
            <h4>Vector Database</h4>
            <p>ChromaDB with HNSW indexing for sub-second retrieval</p>
          </div>
          <div className="spec-item">
            <h4>Embedding Models</h4>
            <p>OpenAI, Hugging Face, and custom fine-tuned models</p>
          </div>
          <div className="spec-item">
            <h4>LLM Integration</h4>
            <p>GPT-4, Claude, Llama, and other leading models</p>
          </div>
          <div className="spec-item">
            <h4>Processing Pipeline</h4>
            <p>Asynchronous processing with progress tracking</p>
          </div>
          <div className="spec-item">
            <h4>Security</h4>
            <p>End-to-end encryption and access control</p>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="about-section">
        <h2>Use Cases & Applications</h2>
        <div className="use-cases">
          <div className="use-case">
            <h4>🔬 Research & Academia</h4>
            <p>Literature review, hypothesis validation, and evidence-based conclusions</p>
          </div>
          <div className="use-case">
            <h4>⚖️ Legal Analysis</h4>
            <p>Case law research, contract analysis, and compliance verification</p>
          </div>
          <div className="use-case">
            <h4>🏥 Healthcare</h4>
            <p>Medical research, treatment validation, and clinical decision support</p>
          </div>
          <div className="use-case">
            <h4>💼 Business Intelligence</h4>
            <p>Market research, competitive analysis, and strategic planning</p>
          </div>
          <div className="use-case">
            <h4>🔧 Technical Documentation</h4>
            <p>API documentation, troubleshooting guides, and knowledge bases</p>
          </div>
          <div className="use-case">
            <h4>🎓 Education</h4>
            <p>Personalized learning, curriculum development, and assessment</p>
          </div>
        </div>
      </section>

      {/* Integration Capabilities */}
      <section className="about-section">
        <h2>Integration & Extensibility</h2>
        <p className="about-text">
          PLUTO is designed for seamless integration with existing workflows:
        </p>
        <div className="integration-features">
          <div className="integration-item">
            <h4>🔗 API-First Design</h4>
            <p>RESTful APIs for easy integration with existing applications</p>
          </div>
          <div className="integration-item">
            <h4>📊 Dashboard Integration</h4>
            <p>Web-based dashboard for monitoring and management</p>
          </div>
          <div className="integration-item">
            <h4>🔌 Plugin System</h4>
            <p>Extensible architecture for custom processing pipelines</p>
          </div>
          <div className="integration-item">
            <h4>☁️ Cloud Deployment</h4>
            <p>Containerized deployment on AWS, Azure, or GCP</p>
          </div>
        </div>
      </section>

      {/* Philosophy */}
      <section className="about-section highlight">
        <h2>Our Philosophy</h2>
        <div className="philosophy-content">
          <p className="about-text philosophy-text">
            <strong className="philosophy-strong">Truth over Confidence:</strong> We'd rather be right than convincing.<br />
            <strong className="philosophy-strong">Transparency over Magic:</strong> Show your work, explain your reasoning.<br />
            <strong className="philosophy-strong">Evidence over Authority:</strong> Sources matter more than credentials.<br />
            <strong className="philosophy-strong">Uncertainty over Certainty:</strong> Know what you don't know.<br />
            <strong className="philosophy-strong">Collaboration over Competition:</strong> Knowledge grows when shared.
          </p>
        </div>
      </section>

      {/* Footer */}
      <section className="about-footer">
        <p>
          PLUTO represents the future of AI: not artificial intelligence that pretends to know everything,
          but augmented intelligence that knows its limitations and works within them.
        </p>
      </section>
      <SplashCursor />
    </div>
  );
};

export default About;
