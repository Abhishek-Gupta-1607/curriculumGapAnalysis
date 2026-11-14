import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Activity,
  Layers,
  CheckCircle2,
  FileText,
  BarChart3,
  BookOpen,
  Cpu
} from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/new-analysis', label: 'New Analysis', icon: PlusCircle },
    { to: '/agent-monitor', label: 'Agent Monitor', icon: Activity },
    { to: '/gaps', label: 'Gap Analysis', icon: Layers },
    { to: '/recommendations', label: 'Recommendations', icon: CheckCircle2 },
    { to: '/reports', label: 'Reports & PDF', icon: FileText },
    { to: '/evaluation', label: 'Benchmark Evaluation', icon: BarChart3 },
    { to: '/frameworks', label: 'Framework Library', icon: BookOpen },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-title">
          <Cpu className="text-primary" size={24} style={{ color: '#6366f1' }} />
          <span>Curriculum AI</span>
          <span className="brand-badge">Multi-Agent</span>
        </div>
        <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 4 }}>
          Semantic Kernel Pipeline
        </div>
      </div>

      <nav className="nav-menu">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end={item.to === '/'}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
          <span style={{ fontWeight: 600, color: '#f8fafc' }}>Local Mode (Offline)</span>
        </div>
        <div>PyMuPDF · ChromaDB · MiniLM</div>
      </div>
    </aside>
  );
}
