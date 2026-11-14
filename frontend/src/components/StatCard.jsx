import React from 'react';

export default function StatCard({ label, value, description, icon: Icon, color = 'primary' }) {
  return (
    <div className="stat-card">
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {description && <div className="stat-desc">{description}</div>}
      </div>
      {Icon && (
        <div className="stat-icon" style={color === 'success' ? { backgroundColor: 'var(--success-bg)', color: 'var(--success)' } : color === 'warning' ? { backgroundColor: 'var(--warning-bg)', color: 'var(--warning)' } : {}}>
          <Icon size={24} />
        </div>
      )}
    </div>
  );
}
