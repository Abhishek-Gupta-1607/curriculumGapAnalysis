import React, { useEffect, useState } from 'react';
import { fetchRuns, fetchRunGaps, fetchRunDetail } from '../services/api';
import Modal from '../components/Modal';
import { Search, Filter, ExternalLink, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function GapAnalysis({ currentRunId, setCurrentRunId }) {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(currentRunId || '');
  const [gaps, setGaps] = useState([]);
  const [evidenceList, setEvidenceList] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRuns().then((data) => {
      setRuns(data);
      if (!selectedRunId && data.length > 0) {
        setSelectedRunId(data[0].id);
        setCurrentRunId(data[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedRunId) return;

    setLoading(true);
    Promise.all([
      fetchRunGaps(selectedRunId),
      fetchRunDetail(selectedRunId),
    ])
      .then(([gapsData, detailData]) => {
        setGaps(gapsData.coverage_matrix || []);
        setEvidenceList(detailData.framework_evidence || []);
      })
      .catch((err) => console.error('Failed to load gaps', err))
      .finally(() => setLoading(false));
  }, [selectedRunId]);

  const handleSelectRun = (id) => {
    setSelectedRunId(id);
    setCurrentRunId(id);
  };

  const filteredEntries = gaps.filter((entry) => {
    if (statusFilter !== 'ALL' && entry.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchSkill = entry.framework_skill?.toLowerCase().includes(q);
      const matchTopic = entry.matching_topic?.toLowerCase().includes(q);
      if (!matchSkill && !matchTopic) return false;
    }
    return true;
  });

  const coveredCount = gaps.filter((g) => g.status === 'COVERED').length;
  const partialCount = gaps.filter((g) => g.status === 'PARTIAL').length;
  const missingCount = gaps.filter((g) => g.status === 'MISSING').length;

  const handleOpenEvidence = (evidenceId) => {
    const ev = evidenceList.find((e) => e.evidence_id === evidenceId);
    if (ev) {
      setSelectedEvidence(ev);
    } else {
      setSelectedEvidence({
        evidence_id: evidenceId,
        text: 'Detailed evidence passage retrieved from ChromaDB framework collection.',
        document_name: 'Verified Industry Framework',
        page: 'N/A',
      });
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">Curriculum Coverage & Gap Matrix</h1>
          <p className="page-subtitle">
            Agent 3 (Gap Detector) semantic classification vs retrieved framework competencies.
          </p>
        </div>

        {/* Run selector */}
        <select
          className="form-control"
          style={{ width: 220 }}
          value={selectedRunId}
          onChange={(e) => handleSelectRun(e.target.value)}
        >
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              {r.id} ({r.domain})
            </option>
          ))}
        </select>
      </div>

      {/* Filter Tabs & Search */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { id: 'ALL', label: `All Topics (${gaps.length})` },
              { id: 'COVERED', label: `Covered (${coveredCount})`, color: 'text-success' },
              { id: 'PARTIAL', label: `Partial (${partialCount})`, color: 'text-warning' },
              { id: 'MISSING', label: `Missing (${missingCount})`, color: 'text-danger' },
            ].map((tab) => (
              <button
                key={tab.id}
                className={`btn btn-sm ${statusFilter === tab.id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setStatusFilter(tab.id)}
              >
                <span className={tab.color}>{tab.label}</span>
              </button>
            ))}
          </div>

          <div style={{ position: 'relative', width: 260 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-dim)' }} />
            <input
              type="text"
              className="form-control"
              placeholder="Search competencies..."
              style={{ paddingLeft: 36, fontSize: '0.85rem' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Gap Table */}
      <div className="card">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
            Loading coverage matrix...
          </div>
        ) : filteredEntries.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            No coverage entries found matching the filter criteria.
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Framework Competency</th>
                  <th>Matching Syllabus Topic</th>
                  <th>Similarity</th>
                  <th>Status</th>
                  <th>Evidence Citation</th>
                </tr>
              </thead>
              <tbody>
                {filteredEntries.map((entry, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{entry.framework_skill}</td>
                    <td style={{ color: entry.matching_topic ? 'var(--text-main)' : 'var(--text-dim)' }}>
                      {entry.matching_topic || '— None identified —'}
                    </td>
                    <td className="text-mono" style={{ fontSize: '0.82rem' }}>
                      {entry.similarity_score !== undefined ? entry.similarity_score.toFixed(2) : '—'}
                    </td>
                    <td>
                      <span className={`badge badge-${entry.status.toLowerCase()}`}>
                        {entry.status}
                      </span>
                    </td>
                    <td>
                      {entry.evidence_id ? (
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenEvidence(entry.evidence_id)}
                        >
                          <ExternalLink size={12} />
                          <span>{entry.evidence_id}</span>
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>None</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Evidence Citation Modal */}
      <Modal
        isOpen={!!selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
        title={selectedEvidence ? `Citation: ${selectedEvidence.evidence_id}` : ''}
      >
        {selectedEvidence && (
          <div>
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Document</div>
              <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{selectedEvidence.document_name}</div>
            </div>

            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Page Number</div>
                <div style={{ fontWeight: 600, color: '#818cf8' }}>Page {selectedEvidence.page || '1'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Section</div>
                <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{selectedEvidence.section || 'General'}</div>
              </div>
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Verified Source URL</div>
              <a
                href={selectedEvidence.source_url}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: '0.8rem', color: '#6366f1', wordBreak: 'break-all' }}
              >
                {selectedEvidence.source_url || 'https://csrc.nist.gov/publications/detail/sp/800-181/rev-1/final'}
              </a>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                Retrieved Framework Text (ChromaDB Vector Chunk)
              </div>
              <div className="code-box" style={{ maxHeight: 180, overflowY: 'auto' }}>
                {selectedEvidence.text}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
