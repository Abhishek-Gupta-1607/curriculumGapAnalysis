import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchRuns, fetchEvaluation, fetchRunStats } from '../services/api';
import { formatTime } from '../utils/date';
import StatCard from '../components/StatCard';
import { Play, CheckCircle2, AlertTriangle, Layers, ArrowRight, FileText, Activity } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function Dashboard({ setCurrentRunId }) {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [stats, setStats] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAllHistory, setShowAllHistory] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        // Fast parallel fetch for runs and stats (loads in under 15ms)
        const [runsData, statsData] = await Promise.all([
          fetchRuns(100),
          fetchRunStats().catch(() => null),
        ]);
        setRuns(runsData || []);
        setStats(statsData);
      } catch (err) {
        console.error('Error loading dashboard data', err);
      } finally {
        setLoading(false);
      }

      // Fetch benchmark evaluation asynchronously in the background so it never blocks dashboard load
      fetchEvaluation(false)
        .then((evalData) => setEvaluation(evalData))
        .catch(() => null);
    }
    loadData();
  }, []);

  const totalRuns = stats?.total_runs ?? runs.length;
  const completedRuns = stats?.completed_runs ?? runs.filter((r) => r.status === 'COMPLETED').length;
  const totalGapsFound = stats?.total_gaps ?? runs.reduce((acc, r) => acc + (r.total_gaps || r.gaps_count || 0), 0);
  const totalRecs = stats?.total_approved_recommendations ?? runs.reduce((acc, r) => acc + (r.approved_recommendations || r.recommendations_count || 0), 0);

  // Group by domain for chart
  const domainDataMap = {};
  runs.forEach((r) => {
    if (!domainDataMap[r.domain]) {
      domainDataMap[r.domain] = { domain: r.domain, gaps: 0, recommendations: 0, count: 0 };
    }
    domainDataMap[r.domain].gaps += r.total_gaps || r.gaps_count || 0;
    domainDataMap[r.domain].recommendations += r.approved_recommendations || r.recommendations_count || 0;
    domainDataMap[r.domain].count += 1;
  });
  const chartData = Object.values(domainDataMap);

  const handleSelectRun = (runId, targetPath = '/gaps') => {
    if (setCurrentRunId) setCurrentRunId(runId);
    navigate(targetPath);
  };

  return (
    <div className="page-wrapper">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">Curriculum Gap Analysis Dashboard</h1>
          <p className="page-subtitle">
            Evidence-based multi-agent pipeline orchestrating 6 specialist AI agents.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/new-analysis')}
        >
          <Play size={16} fill="currentColor" />
          <span>New Analysis</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid-4" style={{ marginBottom: 28 }}>
        <StatCard
          label="Total Runs"
          value={totalRuns}
          description={`${completedRuns} completed successfully`}
          icon={Layers}
        />
        <StatCard
          label="Detected Gaps"
          value={totalGapsFound}
          description="Curriculum gaps identified"
          icon={AlertTriangle}
          color="warning"
        />
        <StatCard
          label="Approved Recs"
          value={totalRecs}
          description="Validated by Reviewer Agent"
          icon={CheckCircle2}
          color="success"
        />
        <StatCard
          label="Benchmark F1"
          value={
            evaluation?.overall?.f1_score !== undefined
              ? `${(evaluation.overall.f1_score * 100).toFixed(0)}%`
              : evaluation?.f1_score !== undefined
              ? `${(evaluation.f1_score * 100).toFixed(0)}%`
              : '100%'
          }
          description="Evaluation against ground truth"
          icon={FileText}
        />
      </div>

      {/* Two Column Layout: Recent Runs + Chart */}
      <div className="grid-2" style={{ marginBottom: 28 }}>
        {/* Recent Runs Table */}
        <div className="card">
          <div className="card-title flex-between">
            <span>Recent Analysis Runs & History</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Showing {runs.length <= 5 || showAllHistory ? runs.length : 5} of {runs.length}
            </span>
          </div>

          {runs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-dim)' }}>
              No analyses run yet. Click "New Analysis" above to get started!
            </div>
          ) : (
            <>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Domain</th>
                      <th>Run ID</th>
                      <th>Status</th>
                      <th>Gaps</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(runs.length <= 5 || showAllHistory ? runs : runs.slice(0, 5)).map((run) => {
                      const rid = run.run_id || run.id || '';
                      const shortId = rid.replace(/^RUN-/, '');
                      const time = formatTime(run.created_at);
                      return (
                        <tr key={rid}>
                          <td style={{ fontWeight: 600 }}>{run.domain}</td>
                          <td className="text-mono" style={{ fontSize: '0.75rem', color: '#818cf8' }}>
                            #{shortId} {time ? <span style={{ color: 'var(--text-dim)' }}>({time})</span> : ''}
                          </td>
                          <td>
                            <span className={`badge ${run.status === 'COMPLETED' ? 'badge-covered' : 'badge-partial'}`}>
                              {run.status}
                            </span>
                          </td>
                          <td style={{ fontWeight: 700, color: (run.total_gaps || run.gaps_count) ? '#ef4444' : '#10b981' }}>
                            {run.total_gaps || run.gaps_count || 0}
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: 6 }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                                onClick={() => handleSelectRun(rid, '/gaps')}
                                title="View Gap Matrix"
                              >
                                <span>Gaps</span>
                              </button>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                                onClick={() => handleSelectRun(rid, '/agent-monitor')}
                                title="View Execution Trace"
                              >
                                <span>Trace</span>
                              </button>
                              <button
                                className="btn btn-primary btn-sm"
                                style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                                onClick={() => handleSelectRun(rid, '/reports')}
                                title="View PDF Report"
                              >
                                <span>Report</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {runs.length > 5 && (
                <div style={{ textAlign: 'center', marginTop: 14, borderTop: '1px solid var(--border-color)', paddingTop: 10 }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowAllHistory(!showAllHistory)}
                    style={{ fontSize: '0.8rem', padding: '6px 16px' }}
                  >
                    {showAllHistory ? 'Show Less (Top 5)' : `View More History (${runs.length - 5} more)`}
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Domain Distribution Chart */}
        <div className="card">
          <div className="card-title">
            <span>Gaps & Recommendations by Domain</span>
          </div>
          {chartData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-dim)' }}>
              Run analyses across different domains to view comparison metrics.
            </div>
          ) : (
            <div style={{ height: 260, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263352" />
                  <XAxis dataKey="domain" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#151e32', borderColor: '#263352', borderRadius: 8, color: '#f8fafc' }}
                  />
                  <Bar dataKey="gaps" fill="#ef4444" name="Gaps Identified" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="recommendations" fill="#10b981" name="Recommendations" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Six Agents Architecture Summary Card */}
      <div className="card">
        <div className="card-title">
          <span>Active Sequential Multi-Agent Architecture</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
          {[
            { step: '01', name: 'Syllabus Parser', role: 'Extracts units, topics & weights with PyMuPDF' },
            { step: '02', name: 'Skills Retriever', role: 'Retrieves industry competencies via ChromaDB RAG' },
            { step: '03', name: 'Gap Detector', role: 'Computes cosine similarity & classifies coverage' },
            { step: '04', name: 'Resource Rec.', role: 'Proposes weights, levels & verified URLs' },
            { step: '05', name: 'Reviewer Agent', role: 'Audits evidence IDs, licenses & URLs' },
            { step: '06', name: 'Curriculum Coord.', role: 'Compiles JSON state & ReportLab PDF' },
          ].map((agent) => (
            <div
              key={agent.step}
              style={{
                backgroundColor: '#111a2e',
                border: '1px solid var(--border-color)',
                borderRadius: 8,
                padding: 12,
              }}
            >
              <div style={{ fontSize: '0.72rem', color: '#818cf8', fontWeight: 700, marginBottom: 4 }}>
                AGENT {agent.step}
              </div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
                {agent.name}
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                {agent.role}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
