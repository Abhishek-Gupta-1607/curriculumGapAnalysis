import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { runAnalysisText, runAnalysisUpload, fetchSamples, fetchSampleContent } from '../services/api';
import { UploadCloud, FileText, Settings, Play, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

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
      if (sampleName.includes('data_science')) setDomain('Data Science');
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

      setCurrentRunId(result.run_id);
      navigate(`/agent-monitor?runId=${result.run_id}`);
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
              <option value="Data Science">Data Science (NIST NICE & ACM CS2023)</option>
              <option value="Web Development">Web Development (ESCO & W3C)</option>
              <option value="Cloud and DevOps">Cloud and DevOps (NIST Cloud Computing)</option>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('data_science.txt')}
              >
                Data Science Syllabus
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('web_development.txt')}
              >
                Web Development Syllabus
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleLoadSample('cloud_devops.txt')}
              >
                Cloud & DevOps Syllabus
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
                <span>Running Sequential Multi-Agent Pipeline...</span>
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
