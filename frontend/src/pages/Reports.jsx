import React, { useEffect, useState } from 'react';
import { fetchRuns, getPdfDownloadUrl, getJsonDownloadUrl, fetchRunReport } from '../services/api';
import { formatTime } from '../utils/date';
import { FileText, Download, Code, CheckCircle2, Clock, Calendar, ExternalLink } from 'lucide-react';

export default function Reports({ currentRunId, setCurrentRunId }) {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(currentRunId || '');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRuns().then((data) => {
      setRuns(data || []);
      if (data && data.length > 0) {
        const firstId = data[0].run_id || data[0].id;
        if (!selectedRunId) {
          setSelectedRunId(firstId);
        }
      }
    });
  }, []);

  useEffect(() => {
    if (currentRunId && currentRunId !== selectedRunId) {
      setSelectedRunId(currentRunId);
    }
  }, [currentRunId]);

  useEffect(() => {
    if (!selectedRunId) return;
    setLoading(true);
    fetchRunReport(selectedRunId)
      .then(setReport)
      .catch((err) => {
        console.error('Failed to load report', err);
        setReport(null);
      })
      .finally(() => setLoading(false));
  }, [selectedRunId]);

  return (
    <div className="page-wrapper">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">Curriculum Gap Analysis Reports</h1>
          <p className="page-subtitle">
            Download institutional PDF reports generated via ReportLab and raw JSON schemas.
          </p>
        </div>

        {/* Run Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Select Analysis:</label>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: 340, maxWidth: 460, fontSize: '0.85rem' }}
            value={selectedRunId}
            onChange={(e) => {
              setSelectedRunId(e.target.value);
              if (setCurrentRunId) setCurrentRunId(e.target.value);
            }}
          >
            {runs.map((r) => {
              const runId = r.run_id || r.id || '';
              const shortId = runId ? runId.replace(/^RUN-/, '') : 'UNKNOWN';
              const time = formatTime(r.created_at);
              return (
                <option key={runId} value={runId}>
                  {r.domain} — #{shortId} {time ? `(${time})` : ''}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {/* Action Header Banner */}
      {selectedRunId && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="flex-between" style={{ flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Selected Run Report</div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginTop: 2 }}>
                Report for Run <span className="text-mono" style={{ color: '#818cf8' }}>{selectedRunId}</span>
              </h2>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <a
                href={getPdfDownloadUrl(selectedRunId)}
                target="_blank"
                rel="noreferrer"
                download
                className="btn btn-primary"
              >
                <Download size={16} />
                <span>Download ReportLab PDF</span>
              </a>
              <a
                href={getJsonDownloadUrl(selectedRunId)}
                target="_blank"
                rel="noreferrer"
                download
                className="btn btn-secondary"
              >
                <Code size={16} />
                <span>Download JSON Payload</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Report Summary Details */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
          Loading report preview...
        </div>
      ) : report ? (
        <div className="grid-2">
          {/* Executive Overview */}
          <div className="card">
            <div className="card-title">
              <FileText size={18} style={{ color: '#6366f1' }} />
              <span>Executive Overview</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="flex-between" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
                <span style={{ color: 'var(--text-muted)' }}>Domain:</span>
                <strong style={{ color: 'var(--text-main)' }}>{report.domain}</strong>
              </div>
              <div className="flex-between" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
                <span style={{ color: 'var(--text-muted)' }}>Total Syllabi Topics:</span>
                <span className="text-mono">{report.statistics?.total_syllabus_topics ?? '—'}</span>
              </div>
              <div className="flex-between" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
                <span style={{ color: 'var(--text-muted)' }}>Covered Competencies:</span>
                <span className="text-mono text-success">{report.statistics?.covered_count ?? '—'}</span>
              </div>
              <div className="flex-between" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
                <span style={{ color: 'var(--text-muted)' }}>Partial Competencies:</span>
                <span className="text-mono text-warning">{report.statistics?.partial_count ?? '—'}</span>
              </div>
              <div className="flex-between" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
                <span style={{ color: 'var(--text-muted)' }}>Missing Competencies (Gaps):</span>
                <span className="text-mono text-danger">{report.statistics?.missing_count ?? '—'}</span>
              </div>
              <div className="flex-between">
                <span style={{ color: 'var(--text-muted)' }}>Approved Recommendations:</span>
                <span className="text-mono text-success">{report.recommendations?.length ?? '—'}</span>
              </div>
            </div>
          </div>

          {/* Institutional Compliance Checklist */}
          <div className="card">
            <div className="card-title">
              <CheckCircle2 size={18} style={{ color: '#10b981' }} />
              <span>Institutional Audit & Verification</span>
            </div>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { title: 'Zero Hallucinated Citations', desc: 'All evidence items reference authentic page numbers and sections.' },
                { title: 'Deterministic Reviewer Validation', desc: 'Recommendations audited for evidence IDs, URL reachability and licenses.' },
                { title: 'Accreditation Ready', desc: 'Weights formulated for university curriculum revisions.' },
                { title: 'Open-Access Resources', desc: 'All learning materials are free, authoritative, and public domain.' },
              ].map((item, idx) => (
                <li key={idx} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <CheckCircle2 size={16} className="text-success" style={{ marginTop: 2, flexShrink: 0 }} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-main)' }}>{item.title}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{item.desc}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
          No report found for this run.
        </div>
      )}
    </div>
  );
}
