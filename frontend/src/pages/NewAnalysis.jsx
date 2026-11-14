import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { runAnalysisText, runAnalysisUpload, fetchSamples, fetchSampleContent } from '../services/api';
import { UploadCloud, FileText, Settings, Play, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

const PIPELINE_STEPS = [
  { num: 1, name: 'Syllabus Parser', desc: 'Extracting course topics, units, and official weights via PyMuPDF...' },
  { num: 2, name: 'Skills Retriever', desc: 'Querying ChromaDB local vector store for authentic industry standards...' },
  { num: 3, name: 'Gap Detector', desc: 'Computing Cosine Similarity & classifying COVERED / PARTIAL / MISSING...' },
  { num: 4, name: 'Resource Recommender', desc: 'Formulating syllabus weight adjustments & verified open-access resources...' },
  { num: 5, name: 'Reviewer Guardrail', desc: 'Deterministic zero-hallucination audit checking citations and licenses...' },
  { num: 6, name: 'Curriculum Coordinator', desc: 'Compiling state serialization & synthesizing ReportLab PDF report...' },
];

export default function NewAnalysis({ setCurrentRunId }) {
  const navigate = useNavigate();
  const [domain, setDomain] = useState('Data Science');
  const [inputMode, setInputMode] = useState('text'); // 'text' | 'file' | 'sample'
  const [syllabusText, setSyllabusText] = useState('');
  const [file, setFile] = useState(null);
  const [coveredThreshold, setCoveredThreshold] = useState(0.75);
  const [partialThreshold, setPartialThreshold] = useState(0.45);
  const [samples, setSamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pipelineStep, setPipelineStep] = useState(1);

  useEffect(() => {
    let timer;
    if (loading) {
      setPipelineStep(1);
      timer = setInterval(() => {
        setPipelineStep((prev) => (prev < 6 ? prev + 1 : 6));
      }, 1200);
    } else {
      setPipelineStep(1);
    }
    return () => clearInterval(timer);
  }, [loading]);

  useEffect(() => {
    fetchSamples()
      .then((data) => setSamples(data.samples || []))
      .catch((err) => console.error('Failed to load samples', err));
  }, []);

  const handleLoadSample = async (sampleName) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSampleContent(sampleName);
      setSyllabusText(data.content);
      if (sampleName.includes('agentic')) setDomain('Agentic AI');
      else if (sampleName.includes('cyber')) setDomain('Cybersecurity');
      else if (sampleName.includes('machine')) setDomain('Machine Learning');
      else if (sampleName.includes('deep')) setDomain('Deep Learning');
      else if (sampleName.includes('full_stack')) setDomain('Full Stack');
      else if (sampleName.includes('data_science')) setDomain('Data Science');
      else if (sampleName.includes('web_development')) setDomain('Web Development');
      else if (sampleName.includes('cloud')) setDomain('Cloud and DevOps');
      setInputMode('text');
    } catch (err) {
      setError(`Failed to load sample: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAnalysis = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let result;
      if (inputMode === 'file') {
        if (!file) {
          throw new Error('Please select a PDF file to upload');
        }
        result = await runAnalysisUpload({
          domain,
          file,
          coveredThreshold,
          partialThreshold,
        });
      } else {
        if (!syllabusText.trim()) {
          throw new Error('Please paste syllabus text or load a sample syllabus');
        }
        result = await runAnalysisText({
          domain,
          text: syllabusText,
          coveredThreshold,
          partialThreshold,
        });
      }

      if (setCurrentRunId) setCurrentRunId(result.run_id);
      navigate(`/agent-monitor?runId=${result.run_id}&animate=true`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <h1 className="page-title">Run New Curriculum Analysis</h1>
        <p className="page-subtitle">
          Submit an academic syllabus to trigger the sequential multi-agent gap detection pipeline.
        </p>
      </div>

      {error && (
        <div style={{ backgroundColor: 'var(--danger-bg)', border: '1px solid var(--danger)', borderRadius: 8, padding: 14, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleStartAnalysis}>
        <div className="grid-3" style={{ marginBottom: 24 }}>
          {/* Domain Selection */}
          <div className="card">
            <label className="form-label">1. Target Academic Domain</label>
            <select
              className="form-control"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
            >
              <option value="Agentic AI">Agentic AI & Multi-Agent Systems (ACM SIGAI)</option>
              <option value="Cybersecurity">Cybersecurity & Ethical Hacking (NIST NICE)</option>
              <option value="Machine Learning">Machine Learning & AI/ML (IEEE & ACM)</option>
              <option value="Deep Learning">Deep Learning & Neural Systems (NeurIPS)</option>
              <option value="Full Stack">Full Stack Web Engineering (W3C & ESCO)</option>
              <option value="Data Science">Data Science & Analytics (NIST & ESCO)</option>
              <option value="Web Development">Web Development & Frontend (W3C Standards)</option>
              <option value="Cloud and DevOps">Cloud Computing & DevOps (NIST SP 500)</option>
            </select>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
              Maps to genuine ChromaDB vector collections with verified industry competencies.
            </p>
          </div>

          {/* Threshold Sliders */}
          <div className="card">
            <label className="form-label">2. Semantic Similarity Thresholds</label>
            <div style={{ marginBottom: 12 }}>
              <div className="flex-between" style={{ fontSize: '0.78rem', marginBottom: 4 }}>
                <span>Covered Threshold:</span>
                <span className="text-mono" style={{ color: '#10b981', fontWeight: 600 }}>{coveredThreshold}</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="0.95"
                step="0.05"
                value={coveredThreshold}
                onChange={(e) => setCoveredThreshold(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--primary)' }}
              />
            </div>
            <div>
              <div className="flex-between" style={{ fontSize: '0.78rem', marginBottom: 4 }}>
                <span>Partial Threshold:</span>
                <span className="text-mono" style={{ color: '#f59e0b', fontWeight: 600 }}>{partialThreshold}</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="0.6"
                step="0.05"
                value={partialThreshold}
                onChange={(e) => setPartialThreshold(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--primary)' }}
              />
            </div>
          </div>

          {/* Sample Preloaders */}
          <div className="card">
            <label className="form-label">3. Quick-Load Benchmark Sample</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('agentic_ai.txt')}
              >
                Agentic AI
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('cybersecurity.txt')}
              >
                Cybersecurity
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('machine_learning.txt')}
              >
                Machine Learning
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('deep_learning.txt')}
              >
                Deep Learning
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('full_stack.txt')}
              >
                Full Stack Web
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('data_science.txt')}
              >
                Data Science
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('cloud_devops.txt')}
              >
                Cloud & DevOps
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('web_development.txt')}
              >
                Web Development
              </button>
            </div>
          </div>
        </div>

        {/* Input Method Switcher */}
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid var(--border-color)', paddingBottom: 16, marginBottom: 20 }}>
            <button
              type="button"
              className={`btn ${inputMode === 'text' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setInputMode('text')}
            >
              <FileText size={16} />
              <span>Paste Syllabus Text</span>
            </button>
            <button
              type="button"
              className={`btn ${inputMode === 'file' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setInputMode('file')}
            >
              <UploadCloud size={16} />
              <span>Upload PDF Document</span>
            </button>
          </div>

          {inputMode === 'text' ? (
            <div className="form-group">
              <label className="form-label">Syllabus Text (Units, Topics, Subtopics & Weights)</label>
              <textarea
                className="form-control"
                rows={12}
                placeholder="Course: Advanced Data Science&#10;Unit 1: Foundations of Machine Learning&#10;- Linear Regression, Logistic Regression (Weight: 20%)&#10;Unit 2: Deep Learning..."
                value={syllabusText}
                onChange={(e) => setSyllabusText(e.target.value)}
              />
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Upload PDF Syllabus</label>
              <input
                type="file"
                accept=".pdf"
                className="form-control"
                onChange={(e) => setFile(e.target.files[0])}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
                PyMuPDF extracts academic units, topic hierarchies, and weight allocations directly from PDF pages.
              </p>
            </div>
          )}
        </div>

        {/* Live Multi-Agent Execution Progress Card */}
        {loading && (
          <div className="card" style={{ marginBottom: 20, backgroundColor: '#0f172a', border: '1px solid #6366f1', padding: 20, boxShadow: '0 8px 24px rgba(99, 102, 241, 0.15)', textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
              <RefreshCw size={22} className="animate-spin" style={{ color: '#818cf8' }} />
              <strong style={{ fontSize: '1.05rem', color: 'var(--text-main)' }}>
                Initializing 6-Agent Sequential Pipeline for {domain}...
              </strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: '#94a3b8', margin: 0 }}>
              Dispatching syllabus to Curriculum Coordinator. Loading live step-by-step execution monitor...
            </p>
          </div>
        )}

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ padding: '14px 28px', fontSize: '1rem' }}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                <span>Launching 6-Agent Pipeline...</span>
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                <span>Start Multi-Agent Analysis</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
