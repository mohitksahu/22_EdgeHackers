import { useEffect, useRef } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import PillNav from "../components/common/PillNav";
import ThemeToggle from "../components/common/ThemeToggle";
import GradientText from "../components/GradientText";
import SpotlightCard from "../components/ui/SpotlightCard";
import ElectricBorder from "../components/ui/ElectricBorder";
import "../styles/Home.css";

export default function Home() {
  const sectionsRef = useRef([]);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.1 }
    );

    sectionsRef.current.forEach((section) => {
      if (section) observer.observe(section);
    });

    return () => observer.disconnect();
  }, []);

  const addToRefs = (el) => {
    if (el && !sectionsRef.current.includes(el)) {
      sectionsRef.current.push(el);
    }
  };

  // Conditionally add back button for about page
  const navItems = location.pathname === '/about' 
    ? [
        { label: '← back home', href: '/' },
        { label: 'new workspace +', href: '/dashboard' }
      ]
    : [
        { label: 'new workspace +', href: '/dashboard' }
      ];

  return (
    <div className="pluto-page">
      <ThemeToggle />
      {/* NAVBAR */}
      <PillNav
        logo=""
        logoAlt="PLUTO Logo"
        items={navItems}
        activeHref="/"
        className="custom-nav"
        ease="power2.easeOut"
      />

      {/* HERO */}
      <section className="pluto-hero fade-in" ref={addToRefs}>
        <h1>
          <GradientText>PLUTO<span>.</span></GradientText>
        </h1>
        <p className="pluto-tagline">Truth needs evidence</p>

        <p className="pluto-subtitle">
          Analyze documents, ask grounded questions, and generate
          evidence-backed insights — all in one workspace.
        </p>

        <div className="pluto-cta">
          <button className="primary-btn" onClick={() => navigate('/dashboard')}>Try PLUTO</button>
          <button className="secondary-btn" onClick={() => navigate('/about')}>Learn more</button>
        </div>
      </section>

      {/* PREVIEW SECTION */}
      <section className="pluto-preview fade-in" ref={addToRefs}>
        <div className="preview-window">
          <div className="preview-header" >PLUTO · Evidence-Grounded Workspace</div>

          <ElectricBorder
            color="var(--electric-border-color, #6366f1)"
            speed={0.8}
            chaos={0.08}
            borderRadius={16}
          >
            <div className="preview-body">
              <div className="preview-chat">
                <div className="chat-line user">
                  <strong>User:</strong> Identify and summarize key findings from the research data
                </div>
                <div className="chat-line ai">
                  <strong style={{fontWeight: '600'}}>PLUTO:</strong> Analysis corroborates three key outcomes, each supported by verifiable source citations and cross-referenced evidence chains.
                </div>
              </div>

              <div className="preview-docs">
                <div className="doc-card">Evidence: Research_Paper.pdf</div>
                <div className="doc-card">Evidence: Market_Report.docx</div>
              </div>
            </div>
          </ElectricBorder>
        </div>
      </section>

      {/* FEATURES */}
      <section className="pluto-features fade-in" ref={addToRefs}>
        <SpotlightCard>
          <div className="feature-card">
            <h3>Evidence-First Answers</h3>
            <p>
              Each answer is backed by verifiable sources, allowing users to inspect
              and trust every conclusion with complete transparency.
            </p>
          </div>
        </SpotlightCard>

        <SpotlightCard>
          <div className="feature-card">
            <h3>Multi-Source Understanding</h3>
            <p>
              Analyze and reason over multiple documents simultaneously, maintaining
              context and accuracy across complex document sets.
            </p>
          </div>
        </SpotlightCard>

        <SpotlightCard>
          <div className="feature-card">
            <h3>Secure by Design</h3>
            <p>
              Your documents remain private, isolated, and never shared across users
              or sessions. Enterprise-grade security built-in.
            </p>
          </div>
        </SpotlightCard>

        <SpotlightCard>
          <div className="feature-card">
            <h3>Advanced Analytics</h3>
            <p>
              Gain deep insights with automated document analysis, trend detection,
              and intelligent summarization powered by cutting-edge AI.
            </p>
          </div>
        </SpotlightCard>

      </section>

      <section className="rag-architecture fade-in" ref={addToRefs}>
        <h2>RAG Architecture Overview</h2>
        <div className="architecture-diagram">
          <div className="component">
            <h4>Vector Store</h4>
            <p>Stores document embeddings for efficient similarity search.</p>
          </div>
          <div className="arrow">→</div>
          <div className="component">
            <h4>Retriever</h4>
            <p>Fetches relevant chunks based on query embeddings.</p>
          </div>
          <div className="arrow">→</div>
          <div className="component">
            <h4>LLM</h4>
            <p>Generates responses using retrieved context.</p>
          </div>
          <div className="arrow">→</div>
          <div className="component">
            <h4>Evidence Ranking</h4>
            <p>Ranks and cites sources for trustworthy answers.</p>
          </div>
        </div>
      </section>

      {/* WHY EVIDENCE MATTERS */}
      <section className="why-evidence fade-in" ref={addToRefs}>
        <h2>Why Evidence Matters</h2>
        <div className="comparison">
          <div className="column">
            <h3>Generic LLM</h3>
            <p>Provides general knowledge responses that may include hallucinations or outdated information.</p>
          </div>
          <div className="column">
            <h3>Evidence-First RAG</h3>
            <p>Delivers grounded, verifiable answers directly linked to your documents, ensuring truth and relevance.</p>
          </div>
        </div>
      </section>

      {/* VIDEO / MOTION SECTION */}
      <section className="video-section fade-in" ref={addToRefs}>
        <div className="video-container">
          <div className="video-player">
            <video 
              controls 
              autoPlay 
              muted 
              loop 
              className="pluto-interface-video"
            >
              <source src="/videos/InShot_20260119_000410803.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
          <p className="video-caption">Experience the PLUTO RAG system interface - where documents meet AI-powered evidence-based reasoning.</p>
        </div>
      </section>

      {/* BUILT FOR RESEARCH & DECISION MAKING */}
      <section className="built-for fade-in" ref={addToRefs}>
        <h2>Built for Research & Decision Making</h2>
        <div className="use-cases">
          <div className="use-case">
            <h3>Research</h3>
            <p>Accelerate literature reviews with evidence-traced summaries.</p>
          </div>
          <div className="use-case">
            <h3>Legal Analysis</h3>
            <p>Ensure compliance and accuracy in legal document review.</p>
          </div>
          <div className="use-case">
            <h3>Policy Review</h3>
            <p>Ground policy decisions in comprehensive document analysis.</p>
          </div>
          <div className="use-case">
            <h3>Technical Documentation</h3>
            <p>Navigate complex technical docs with precise, sourced answers.</p>
          </div>
          <div className="use-case">
            <h3>Business Intelligence</h3>
            <p>Extract actionable insights from market reports and financial data.</p>
          </div>
          <div className="use-case">
            <h3>Healthcare Analysis</h3>
            <p>Analyze medical research and patient data with evidence-based accuracy.</p>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="final-cta fade-in" ref={addToRefs}>
        <h2>Start with Evidence</h2>
        <p>Experience the power of grounded AI reasoning.</p>
        <Link to="/about" className="cta-button-link">
          <button className="cta-button">Learn More About PLUTO</button>
        </Link>
      </section>

      {/* PLUTO DECORATIVE */}
      <section className="pluto-decorative">
        <div className="decorative-content">
          <div className="pluto-symbol">P</div>
          <div className="pluto-symbol">L</div>
          <div className="pluto-symbol">U</div>
          <div className="pluto-symbol">T</div>
          <div className="pluto-symbol">O</div>
        </div>
        <p className="decorative-text">Truth needs evidence</p>
        <div className="decorative-subtitle">
          <span>Retrieval-Augmented Generation</span>
          <span>•</span>
          <span>Evidence-Based AI</span>
          <span>•</span>
          <span>Document Intelligence</span>
        </div>
      </section>
    </div>
  );
}
