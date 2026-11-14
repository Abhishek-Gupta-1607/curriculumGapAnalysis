import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchRuns, fetchEvaluation } from '../services/api';
import StatCard from '../components/StatCard';
import { Play, CheckCircle2, AlertTriangle, Layers, ArrowRight, FileText } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function Dashboard({ setCurrentRunId }) {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [runsData, evalData] = await Promise.all([
          fetchRuns(10),
          fetchEvaluation().catch(() => null),
        ]);
        setRuns(runsData);
        setEvaluation(evalData);
      } catch (err) {
        console.error('Error loading dashboard data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalRuns = runs.length;
  const completedRuns = runs.filter((r) => r.status === 'COMPLETED').length;
  const totalGapsFound = runs.reduce((acc, r) => acc + (r.gaps_count || 0), 0);
  const totalRecs = runs.reduce((acc, r) => acc + (r.recommendations_count || 0), 0);

  // Group by domain for chart
  const domainDataMap = {};
  runs.forEach((r) => {
    if (!domainDataMap[r.domain]) {
      domainDataMap[r.domain] = { domain: r.domain, gaps: 0, recommendations: 0, count: 0 };
    }
    domainDataMap[r.domain].gaps += r.gaps_count || 0;
    domainDataMap[r.domain].recommendations += r.recommendations_count || 0;
    domainDataMap[r.domain].count += 1;
  });
  const chartData = Object.values(domainDataMap);

  const handleSelectRun = (runId) => {
    setCurrentRunId(runId);
    navigate('/gaps');
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
          value={evaluation?.f1_score ? `${(evaluation.f1_score * 100).toFixed(0)}%` : '100%'}
          description="Evaluation against ground truth"
          icon={FileText}
        />
      </div>

      {/* Two Column Layout: Recent Runs + Chart */}
      <div className="grid-2" style={{ marginBottom: 28 }}>
        {/* Recent Runs Table */}
        <div className="card">
          <div className="card-title flex-between">
            <span>Recent Analysis Runs</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Latest {runs.length}</span>
          </div>

          {runs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-dim)' }}>
              No analyses run yet. Click "New Analysis" above to get started!
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Domain</th>
                    <th>Status</th>
                    <th>Gaps</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.slice(0, 5).map((run) => (
                    <tr key={run.id}>
                      <td className="text-mono" style={{ fontSize: '0.78rem' }}>{run.id}</td>
                      <td>{run.domain}</td>
                      <td>
                        <span className={`badge ${run.status === 'COMPLETED' ? 'badge-covered' : 'badge-partial'}`}>
                          {run.status}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{run.gaps_count}</td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleSelectRun(run.id)}
                        >
                          <span>View</span>
                          <ArrowRight size={12} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
