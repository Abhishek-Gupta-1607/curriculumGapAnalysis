import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { fetchRuns, fetchRunEvents, fetchRunDetail } from '../services/api';
import { formatTime } from '../utils/date';
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
  FileCheck,
  Play,
  RotateCcw
} from 'lucide-react';

const AGENT_ICON_MAP = {
  syllabusparser: FileCheck,
  syllabus_parser: FileCheck,
  skillsretriever: Database,
  skills_retriever: Database,
  gapdetector: Search,
  gap_detector: Search,
  resourcerecommender: BookOpen,
  resource_recommender: BookOpen,
  reviewer: ShieldCheck,
  revieweragent: ShieldCheck,
  curriculumcoordinator: Cpu,
  coordinator: Cpu,
};

const AGENT_RUNNING_DESCRIPTIONS = {
  1: 'Analyzing syllabus structure, extracting units, topics, and credit weight allocations via PyMuPDF...',
  2: 'Querying local ChromaDB vector database with all-MiniLM-L6-v2 embeddings for verified industry standards...',
  3: 'Computing semantic cosine similarity & classifying competencies (COVERED / PARTIAL / MISSING)...',
  4: 'Formulating syllabus weight adjustments, lecture hours, and verified open-access resources...',
  5: 'Reviewer Guardrail executing deterministic audit for zero-hallucinated citations & licenses...',
  6: 'Curriculum Coordinator serializing workflow state to database and compiling ReportLab PDF...',
};

function getAgentIcon(name) {
  if (!name) return Cpu;
  const key = name.toLowerCase().replace(/[^a-z]/g, '');
  return AGENT_ICON_MAP[key] || Cpu;
}

function formatAgentName(name) {
  if (!name) return 'Specialist Agent';
  return name.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');
}

export default function AgentMonitor({ currentRunId, setCurrentRunId }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const activeId = searchParams.get('runId') || currentRunId;
  const initialAnimate = searchParams.get('animate') === 'true';

  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(activeId || '');
  const [events, setEvents] = useState([]);
  const [runDetail, setRunDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [inspectEvent, setInspectEvent] = useState(null);

  // Progressive Step-by-Step Execution State
  const [isAnimating, setIsAnimating] = useState(initialAnimate);
  const [animatedStep, setAnimatedStep] = useState(initialAnimate ? 1 : 999);
  const animationTriggeredRef = useRef(false);

  useEffect(() => {
    fetchRuns().then((data) => {
      setRuns(data || []);
      if (!selectedRunId && data && data.length > 0) {
        const firstId = data[0].run_id || data[0].id;
        setSelectedRunId(firstId);
        if (setCurrentRunId) setCurrentRunId(firstId);
      }
    });
  }, []);

  useEffect(() => {
    if (activeId && activeId !== selectedRunId) {
      setSelectedRunId(activeId);
    }
  }, [activeId]);

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
          const traceList = Array.isArray(eventsData)
            ? eventsData
            : (eventsData?.events || []);
          setEvents(traceList);
          setRunDetail(detailData);

          // If coming with animate=true parameter, start live progression
          if (initialAnimate && !animationTriggeredRef.current) {
            animationTriggeredRef.current = true;
            setIsAnimating(true);
            setAnimatedStep(1);
          } else if (!isAnimating) {
            setAnimatedStep(999);
          }
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

  // Progressive multi-agent step advancement timer
  useEffect(() => {
    if (!isAnimating || events.length === 0) return;

    if (animatedStep > events.length) {
      setIsAnimating(false);
      return;
    }

    const timer = setTimeout(() => {
      setAnimatedStep((prev) => {
        if (prev >= events.length) {
          setIsAnimating(false);
          return events.length + 1;
        }
        return prev + 1;
      });
    }, 1150);

    return () => clearTimeout(timer);
  }, [isAnimating, animatedStep, events.length]);

  const handleSelectRun = (id) => {
    setIsAnimating(false);
    setAnimatedStep(999);
    setSelectedRunId(id);
    if (setCurrentRunId) setCurrentRunId(id);
  };

  const handleReplay = () => {
    setAnimatedStep(1);
    setIsAnimating(true);
  };

  const handleSkipAnimation = () => {
    setIsAnimating(false);
    setAnimatedStep(events.length + 1);
  };

  const totalSteps = events.length || 6;
  const currentActiveStep = Math.min(animatedStep, totalSteps);
  const currentActiveEvent = events[currentActiveStep - 1];

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

      {/* Live Pipeline Execution Progress Banner (When Running) */}
      {isAnimating ? (
        <div className="card" style={{ marginBottom: 24, backgroundColor: '#070c17', border: '1px solid var(--primary)', padding: 20, boxShadow: '0 8px 30px rgba(37, 99, 235, 0.25)' }}>
          <div className="flex-between" style={{ flexWrap: 'wrap', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: '50%', backgroundColor: 'rgba(37, 99, 235, 0.2)', border: '2px solid var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <RefreshCw size={22} className="animate-spin" style={{ color: '#3b82f6' }} />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-main)' }}>
                    Executing Sequential Multi-Agent Pipeline
                  </span>
                  <span className="badge badge-primary" style={{ fontSize: '0.78rem' }}>
                    Agent {currentActiveStep} of {totalSteps}
                  </span>
                </div>
                <div style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: 4 }}>
                  Active Agent:{' '}
                  <strong style={{ color: '#60a5fa' }}>
                    {currentActiveEvent ? formatAgentName(currentActiveEvent.agent_name) : `Step ${currentActiveStep}`}
                  </strong>
                  {' — '}
                  <span>{AGENT_RUNNING_DESCRIPTIONS[currentActiveStep] || 'Processing stage...'}</span>
                </div>
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              onClick={handleSkipAnimation}
              title="Fast-forward to completed results"
            >
              <span>Skip to Results</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {/* Animated Progress Bar */}
          <div style={{ width: '100%', height: 6, backgroundColor: '#0c1322', borderRadius: 3, overflow: 'hidden', marginTop: 16 }}>
            <div
              style={{
                width: `${(currentActiveStep / totalSteps) * 100}%`,
                height: '100%',
                backgroundColor: 'var(--primary)',
                boxShadow: '0 0 10px rgba(37, 99, 235, 0.7)',
                transition: 'width 0.8s ease-in-out',
              }}
            />
          </div>
        </div>
      ) : (
        /* Completed Results Summary Banner (Revealed After All Agents Finish) */
        runDetail && (
          <div className="card" style={{ marginBottom: 24, backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
            <div className="flex-between" style={{ flexWrap: 'wrap', gap: 16 }}>
              <div style={{ display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Domain</span>
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>{runDetail.domain}</div>
                </div>
                <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: 24 }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Pipeline Status</span>
                  <div>
                    <span className="badge badge-covered" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <CheckCircle2 size={13} />
                      ALL {totalSteps} AGENTS COMPLETED
                    </span>
                  </div>
                </div>
                <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: 24 }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Gaps Identified</span>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#ef4444' }}>{runDetail.gaps?.length || 0}</div>
                </div>
                <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: 24 }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reviewer Approved</span>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#a3e635' }}>{runDetail.recommendations?.length || 0}</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleReplay}
                  title="Replay live step-by-step pipeline execution"
                >
                  <RotateCcw size={14} />
                  <span>Replay Pipeline</span>
                </button>
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
        )
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
              const Icon = getAgentIcon(evt.agent_name);
              const formattedName = formatAgentName(evt.agent_name);
              const stepNum = evt.step_number || (idx + 1);

              const isCompleted = !isAnimating || stepNum < animatedStep;
              const isRunning = isAnimating && stepNum === animatedStep;
              const isPending = isAnimating && stepNum > animatedStep;

              return (
                <div key={evt.event_id || evt.id || idx} className="timeline-item">
                  {/* Icon Box */}
                  <div
                    className={`timeline-icon-box ${
                      isCompleted ? 'completed' : isRunning ? 'running' : 'pending'
                    }`}
                  >
                    {isRunning ? (
                      <RefreshCw size={20} className="animate-spin" style={{ color: '#818cf8' }} />
                    ) : (
                      <Icon size={20} style={{ opacity: isPending ? 0.35 : 1 }} />
                    )}
                  </div>

                  {/* Content Box */}
                  <div
                    className={`timeline-content ${
                      isRunning ? 'running' : isPending ? 'pending' : ''
                    }`}
                  >
                    <div className="flex-between" style={{ marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: isPending ? 'var(--text-dim)' : 'var(--text-main)' }}>
                          Step {stepNum}: {formattedName}
                        </span>

                        {isCompleted && (
                          <span className="badge badge-covered" style={{ fontSize: '0.7rem' }}>
                            <CheckCircle2 size={12} />
                            COMPLETED
                          </span>
                        )}

                        {isRunning && (
                          <span
                            className="badge"
                            style={{
                              fontSize: '0.7rem',
                              backgroundColor: '#2563eb',
                              color: '#ffffff',
                              border: '1px solid #3b82f6',
                              boxShadow: '0 0 10px rgba(37, 99, 235, 0.45)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 5,
                            }}
                          >
                            <RefreshCw size={11} className="animate-spin" />
                            RUNNING
                          </span>
                        )}

                        {isPending && (
                          <span
                            className="badge"
                            style={{
                              fontSize: '0.7rem',
                              backgroundColor: '#0c1322',
                              color: 'var(--text-dim)',
                              border: '1px solid #1e2e4a',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 5,
                            }}
                          >
                            <Clock size={11} />
                            QUEUED
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          {isCompleted ? (
                            <>
                              <Clock size={13} />
                              <span>{evt.duration_ms !== undefined ? `${evt.duration_ms} ms` : '< 50 ms'}</span>
                            </>
                          ) : isRunning ? (
                            <span style={{ color: '#60a5fa', fontStyle: 'italic' }}>Active Execution...</span>
                          ) : (
                            <span style={{ color: 'var(--text-dim)' }}>Pending...</span>
                          )}
                        </div>

                        {isCompleted && (
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                            onClick={() => setInspectEvent(evt)}
                          >
                            <Code size={12} />
                            <span>Inspect Payload</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Step State Descriptions */}
                    {isCompleted && (
                      <>
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                          <strong>Output:</strong> {evt.output_summary}
                        </div>
                        {evt.input_summary && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 4 }}>
                            <strong>Input:</strong> {evt.input_summary}
                          </div>
                        )}
                      </>
                    )}

                    {isRunning && (
                      <>
                        <div style={{ fontSize: '0.84rem', color: '#c7d2fe', lineHeight: 1.5, fontWeight: 500 }}>
                          <strong>Active Task:</strong> {AGENT_RUNNING_DESCRIPTIONS[stepNum] || 'Processing stage...'}
                        </div>
                        {evt.input_summary && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 6 }}>
                            <strong>Input Context:</strong> {evt.input_summary}
                          </div>
                        )}
                      </>
                    )}

                    {isPending && (
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                        Waiting for Step {stepNum - 1} agent to complete sequential data handoff...
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
        title={inspectEvent ? `Agent Trace: ${formatAgentName(inspectEvent.agent_name)} (Step ${inspectEvent.step_number})` : ''}
      >
        {inspectEvent && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4 }}>Agent:</div>
              <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{formatAgentName(inspectEvent.agent_name)}</div>
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
              Event Timestamp: {new Date(inspectEvent.finished_at || inspectEvent.started_at || inspectEvent.created_at || Date.now()).toLocaleString()}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
