import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { fetchRuns, fetchRunEvents, fetchRunDetail } from '../services/api';
import Modal from '../components/Modal';
import {
  CheckCircle2,
  Clock,
  Code,
  ArrowRight,
  RefreshCw,
  Cpu,
  Database,
  Search,
  BookOpen,
  ShieldCheck,
  FileCheck
} from 'lucide-react';

const AGENT_ICONS = {
  syllabus_parser: FileCheck,
  skills_retriever: Database,
  gap_detector: Search,
  resource_recommender: BookOpen,
  reviewer: ShieldCheck,
  coordinator: Cpu,
};

export default function AgentMonitor({ currentRunId, setCurrentRunId }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const activeId = searchParams.get('runId') || currentRunId;

  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(activeId || '');
  const [events, setEvents] = useState([]);
  const [runDetail, setRunDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [inspectEvent, setInspectEvent] = useState(null);

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

    let isMounted = true;
    setLoading(true);

    async function loadTrace() {
      try {
        const [eventsData, detailData] = await Promise.all([
          fetchRunEvents(selectedRunId),
          fetchRunDetail(selectedRunId),
        ]);
        if (isMounted) {
          setEvents(eventsData.events || []);
          setRunDetail(detailData);
        }
      } catch (err) {
        console.error('Failed to load trace events', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadTrace();
    return () => { isMounted = false; };
  }, [selectedRunId]);

  const handleSelectRun = (id) => {
    setSelectedRunId(id);
    setCurrentRunId(id);
  };

  return (
    <div className="page-wrapper">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">Multi-Agent Execution Trace</h1>
          <p className="page-subtitle">
            Real-time telemetry and execution logs across all 6 Semantic Kernel agents.
          </p>
        </div>

        {/* Run Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Select Run:</label>
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
      </div>

      {/* Run Summary Banner */}
      {runDetail && (
        <div className="card" style={{ marginBottom: 24, backgroundColor: '#111a2e' }}>
          <div className="flex-between">
            <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Domain</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>{runDetail.domain}</div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: 24 }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Status</span>
                <div>
                  <span className={`badge ${runDetail.status === 'COMPLETED' ? 'badge-covered' : 'badge-partial'}`}>
                    {runDetail.status}
                  </span>
                </div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: 24 }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Gaps Identified</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: '#ef4444' }}>{runDetail.gaps?.length || 0}</div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: 24 }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reviewer Approved</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: '#10b981' }}>{runDetail.recommendations?.length || 0}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/gaps')}>
                <span>View Gap Matrix</span>
                <ArrowRight size={14} />
              </button>
              <button className="btn btn-primary btn-sm" onClick={() => navigate('/reports')}>
                <span>View PDF Report</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agents Sequential Timeline */}
      <div className="card">
        <div className="card-title flex-between">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Cpu size={20} style={{ color: '#6366f1' }} />
            <span>Sequential Agent Execution Pipeline</span>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Recorded in SQLite Database (agent_events table)
          </span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
            <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 12px' }} />
            <div>Loading agent execution telemetry...</div>
          </div>
        ) : events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            No trace events found for this run.
          </div>
        ) : (
          <div className="timeline">
            {events.map((evt, idx) => {
              const Icon = AGENT_ICONS[evt.agent_name] || Cpu;
              return (
                <div key={evt.id || idx} className="timeline-item">
                  <div className="timeline-icon-box completed">
                    <Icon size={20} />
                  </div>
                  <div className="timeline-content">
                    <div className="flex-between" style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)', textTransform: 'capitalize' }}>
                          Step {evt.step_number}: {evt.agent_name.replace('_', ' ')}
                        </span>
                        <span className="badge badge-covered" style={{ fontSize: '0.7rem' }}>
                          <CheckCircle2 size={12} />
                          {evt.status}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          <Clock size={13} />
                          <span>{evt.duration_ms ? `${evt.duration_ms} ms` : '< 50 ms'}</span>
                        </div>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                          onClick={() => setInspectEvent(evt)}
                        >
                          <Code size={12} />
                          <span>Inspect Payload</span>
                        </button>
                      </div>
                    </div>

                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      <strong>Output:</strong> {evt.output_summary}
                    </div>

                    {evt.input_summary && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 4 }}>
                        <strong>Input:</strong> {evt.input_summary}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Inspect Modal */}
      <Modal
        isOpen={!!inspectEvent}
        onClose={() => setInspectEvent(null)}
        title={inspectEvent ? `Agent Trace: ${inspectEvent.agent_name} (Step ${inspectEvent.step_number})` : ''}
      >
        {inspectEvent && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4 }}>Agent Name:</div>
              <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{inspectEvent.agent_name}</div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4 }}>Execution Latency:</div>
              <div style={{ fontWeight: 600, color: '#10b981' }}>{inspectEvent.duration_ms} milliseconds</div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4 }}>Input Summary:</div>
              <div className="code-box">{inspectEvent.input_summary || 'None'}</div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4 }}>Output Summary:</div>
              <div className="code-box">{inspectEvent.output_summary || 'None'}</div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 12 }}>
              Timestamp: {new Date(inspectEvent.created_at).toLocaleString()}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
