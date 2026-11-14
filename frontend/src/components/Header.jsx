import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../services/api';
import { ShieldCheck, Database, Server } from 'lucide-react';

export default function Header({ currentRunId, onSelectRun }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.error('Health fetch failed', err));
  }, []);

  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ fontSize: '0.88rem', color: '#94a3b8' }}>
          Active Run:
        </span>
        <span className="badge badge-primary" style={{ fontFamily: 'var(--font-mono)' }}>
          {currentRunId || 'No active run'}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: '#94a3b8' }}>
          <Server size={14} />
          <span>Semantic Kernel:</span>
          <span style={{ color: '#10b981', fontWeight: 600 }}>Ready</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: '#94a3b8' }}>
          <Database size={14} />
          <span>Vector DB:</span>
          <span style={{ color: '#818cf8', fontWeight: 600 }}>ChromaDB Local</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: '#94a3b8' }}>
          <ShieldCheck size={14} />
          <span>Reviewer Audit:</span>
          <span style={{ color: '#10b981', fontWeight: 600 }}>Active</span>
        </div>
      </div>
    </header>
  );
}
