import React, { useState, Component } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

import Dashboard from './pages/Dashboard';
import NewAnalysis from './pages/NewAnalysis';
import AgentMonitor from './pages/AgentMonitor';
import GapAnalysis from './pages/GapAnalysis';
import Recommendations from './pages/Recommendations';
import Reports from './pages/Reports';
import Evaluation from './pages/Evaluation';
import FrameworkLibrary from './pages/FrameworkLibrary';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: '#f8fafc', background: '#0b1120', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ maxWidth: 550, background: '#151e32', border: '1px solid #ef4444', borderRadius: 12, padding: 24, textAlign: 'center' }}>
            <h2 style={{ color: '#ef4444', marginBottom: 12, fontSize: '1.25rem' }}>An error occurred in this view</h2>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginBottom: 16 }}>
              {this.state.error?.message || "Unexpected UI rendering issue."}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false });
                window.location.href = '/';
              }}
              style={{ background: '#6366f1', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [currentRunId, setCurrentRunId] = useState(null);

  return (
    <Router>
      <ErrorBoundary>
        <div className="app-container">
          <Sidebar />
          <div className="main-content">
            <Header currentRunId={currentRunId} onSelectRun={setCurrentRunId} />
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<Dashboard setCurrentRunId={setCurrentRunId} />} />
                <Route path="/new-analysis" element={<NewAnalysis setCurrentRunId={setCurrentRunId} />} />
                <Route path="/agent-monitor" element={<AgentMonitor currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
                <Route path="/gaps" element={<GapAnalysis currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
                <Route path="/recommendations" element={<Recommendations currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
                <Route path="/reports" element={<Reports currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
                <Route path="/evaluation" element={<Evaluation />} />
                <Route path="/frameworks" element={<FrameworkLibrary />} />
              </Routes>
            </ErrorBoundary>
          </div>
        </div>
      </ErrorBoundary>
    </Router>
  );
}
