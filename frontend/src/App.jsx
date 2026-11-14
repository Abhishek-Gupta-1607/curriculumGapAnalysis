import React, { useState } from 'react';
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

export default function App() {
  const [currentRunId, setCurrentRunId] = useState(null);

  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Header currentRunId={currentRunId} onSelectRun={setCurrentRunId} />
          <Routes>
            <Route path="/" element={<Dashboard setCurrentRunId={setCurrentRunId} />} />
            <Route path="/new-analysis" element={<NewAnalysis setCurrentRunId={setCurrentRunId} />} />
            <Route path="/agent-monitor" element={<AgentMonitor currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
            <Route path="/gaps" element={<GapAnalysis currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
            <Route path="/recommendations" element={<Recommendations currentRunId={currentRunId} setCurrentRunId={setCurrentRunId} />} />
            <Route path="/reports" element={<Reports currentRunId={currentRunId} />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route path="/frameworks" element={<FrameworkLibrary />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
