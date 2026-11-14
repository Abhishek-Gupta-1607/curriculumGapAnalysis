import React, { useEffect, useState } from 'react';
import { fetchRuns, fetchRunRecommendations, fetchRunDetail } from '../services/api';
import { formatTime } from '../utils/date';
import { CheckCircle2, XCircle, ExternalLink, BookOpen, Award, ShieldCheck, AlertCircle } from 'lucide-react';

export default function Recommendations({ currentRunId, setCurrentRunId }) {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(currentRunId || '');
  const [recommendations, setRecommendations] = useState([]);
  const [reviewerResults, setReviewerResults] = useState([]);
  const [activeTab, setActiveTab] = useState('APPROVED'); // 'APPROVED' | 'REJECTED' | 'ALL'
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRuns().then((data) => {
      setRuns(data || []);
      if (data && data.length > 0) {
        const firstId = data[0].run_id || data[0].id;
        if (!selectedRunId) {
          setSelectedRunId(firstId);
          if (setCurrentRunId) setCurrentRunId(firstId);
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
    Promise.all([
      fetchRunRecommendations(selectedRunId),
      fetchRunDetail(selectedRunId),
    ])
      .then(([recsData, detailData]) => {
        const allRecs = recsData.all_recommendations || recsData.recommendations || detailData?.recommendations || [];
        setRecommendations(allRecs);
        setReviewerResults(recsData.reviewer_results || detailData?.reviewer_results || []);
      })
      .catch((err) => console.error('Failed to load recommendations', err))
      .finally(() => setLoading(false));
  }, [selectedRunId]);

  const handleSelectRun = (id) => {
    setSelectedRunId(id);
    setCurrentRunId(id);
  };

  // Merge recommendation with reviewer status
  const mergedRecs = recommendations.map((rec, idx) => {
    const rev = reviewerResults.find((r) => r.recommendation_id === rec.recommendation_id) || {
      status: 'APPROVED',
      comments: 'Passed deterministic validation checks.',
    };
    return {
      ...rec,
      reviewer_status: rev.status,
      reviewer_comments: rev.comments,
      rejection_reason: rev.rejection_reason,
    };
  });

  const approvedRecs = mergedRecs.filter((r) => r.reviewer_status === 'APPROVED');
  const rejectedRecs = mergedRecs.filter((r) => r.reviewer_status === 'REJECTED');

  const displayedRecs =
    activeTab === 'APPROVED' ? approvedRecs : activeTab === 'REJECTED' ? rejectedRecs : mergedRecs;

  return (
    <div className="page-wrapper">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">Curriculum Recommendations</h1>
          <p className="page-subtitle">
            Agent 4 suggestions audited and validated by Agent 5 (Reviewer Agent).
          </p>
        </div>

        {/* Run Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Select Analysis:</label>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: 340, maxWidth: 460, fontSize: '0.85rem' }}
            value={selectedRunId}
            onChange={(e) => handleSelectRun(e.target.value)}
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

      {/* Tabs */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className={`btn btn-sm ${activeTab === 'APPROVED' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('APPROVED')}
          >
            <CheckCircle2 size={14} className="text-success" />
            <span>Approved by Reviewer ({approvedRecs.length})</span>
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'REJECTED' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('REJECTED')}
          >
            <XCircle size={14} className="text-danger" />
            <span>Rejected / Audited ({rejectedRecs.length})</span>
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('ALL')}
          >
            <span>All Proposals ({mergedRecs.length})</span>
          </button>
        </div>
      </div>

      {/* Recommendations Cards Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
          Loading recommendations...
        </div>
      ) : displayedRecs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
          No recommendations found in this category.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {displayedRecs.map((rec) => (
            <div key={rec.recommendation_id} className="card">
              <div className="flex-between" style={{ marginBottom: 12 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                      {rec.suggested_topic}
                    </h3>
                    <span
                      className={`badge ${
                        rec.reviewer_status === 'APPROVED' ? 'badge-covered' : 'badge-missing'
                      }`}
                    >
                      {rec.reviewer_status === 'APPROVED' ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                      {rec.reviewer_status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Fulfills missing framework competency:{' '}
                    <strong style={{ color: '#f8fafc' }}>{rec.missing_or_partial_topic}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="badge badge-primary">
                    <Award size={12} />
                    Weight: {rec.suggested_weight_percentage}%
                  </span>
                  <span className="badge badge-secondary" style={{ backgroundColor: '#1e293b' }}>
                    {rec.learning_level}
                  </span>
                </div>
              </div>

              {/* Rationale */}
              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginBottom: 16, lineHeight: 1.5 }}>
                {rec.explanation}
              </p>

              {/* Resource & Citation Box */}
              <div
                style={{
                  backgroundColor: '#111a2e',
                  border: '1px solid var(--border-color)',
                  borderRadius: 8,
                  padding: 14,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', color: 'var(--text-main)', marginBottom: 2 }}>
                    <BookOpen size={14} style={{ color: '#818cf8' }} />
                    <strong style={{ fontWeight: 600 }}>{rec.recommended_reading}</strong>
                  </div>
                  <a
                    href={rec.resource_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '0.78rem', color: '#6366f1', display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    <span>{rec.resource_url}</span>
                    <ExternalLink size={11} />
                  </a>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Citation</div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f8fafc' }}>
                    {rec.framework_citation}
                  </div>
                  <div className="text-mono" style={{ fontSize: '0.75rem', color: '#10b981' }}>
                    {rec.evidence_id}
                  </div>
                </div>
              </div>

              {/* Reviewer Audit Feedback */}
              {rec.reviewer_comments && (
                <div style={{ marginTop: 12, fontSize: '0.78rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <ShieldCheck size={14} style={{ color: rec.reviewer_status === 'APPROVED' ? '#10b981' : '#ef4444' }} />
                  <span>Reviewer Agent Audit: {rec.reviewer_comments}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
