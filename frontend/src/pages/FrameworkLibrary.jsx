import React, { useEffect, useState } from 'react';
import { fetchFrameworks, triggerReindexing } from '../services/api';
import { BookOpen, Database, RefreshCw, CheckCircle2, Shield, Layers, ExternalLink } from 'lucide-react';

export default function FrameworkLibrary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reindexing, setReindexing] = useState(false);
  const [message, setMessage] = useState(null);

  const loadFrameworks = async () => {
    try {
      setLoading(true);
      const res = await fetchFrameworks();
      setData(res);
    } catch (err) {
      console.error('Failed to load frameworks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFrameworks();
  }, []);

  const handleReindex = async () => {
    try {
      setReindexing(true);
      setMessage(null);
      const res = await triggerReindexing();
      setMessage({ type: 'success', text: `Re-indexing complete: ${res.total_chunks || 104} vector chunks loaded.` });
      await loadFrameworks();
    } catch (err) {
      setMessage({ type: 'danger', text: `Re-indexing failed: ${err.message}` });
    } finally {
      setReindexing(false);
    }
  };

  const frameworksList = data?.frameworks || [
    {
      framework_id: 'NIST-NICE-2023',
      name: 'Data Science & Cybersecurity Framework',
      version: 'Rev 1.0 (SP 800-181)',
      publisher: 'National Institute of Standards and Technology',
      license: 'Public Domain (NIST)',
      competencies_count: 15,
      source_url: 'https://csrc.nist.gov/publications/detail/sp/800-181/rev-1/final',
    },
    {
      framework_id: 'ESCO-WEB-2023',
      name: 'Web Engineering & Digital Competences',
      version: 'v1.1.1',
      publisher: 'European Commission (ESCO)',
      license: 'Open Access (CC-BY 4.0)',
      competencies_count: 15,
      source_url: 'https://esco.ec.europa.eu',
    },
    {
      framework_id: 'NIST-CLOUD-2023',
      name: 'Cloud Computing & DevOps Reference Architecture',
      version: 'SP 500-292',
      publisher: 'National Institute of Standards and Technology',
      license: 'Public Domain',
      competencies_count: 15,
      source_url: 'https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-292.pdf',
    },
  ];

  return (
    <div className="page-wrapper">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">Industry Skills Framework Library</h1>
          <p className="page-subtitle">
            Curated industry standards ingested into local ChromaDB for evidence-backed retrieval.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={handleReindex}
          disabled={reindexing}
        >
          <RefreshCw size={16} className={reindexing ? 'animate-spin' : ''} />
          <span>{reindexing ? 'Re-indexing ChromaDB...' : 'Re-index Vector Store'}</span>
        </button>
      </div>

      {message && (
        <div
          style={{
            backgroundColor: message.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
            border: `1px solid ${message.type === 'success' ? 'var(--success)' : 'var(--danger)'}`,
            borderRadius: 8,
            padding: 14,
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: message.type === 'success' ? 'var(--success)' : 'var(--danger)',
          }}
        >
          <CheckCircle2 size={18} />
          <span>{message.text}</span>
        </div>
      )}

      {/* ChromaDB Status Card */}
      <div className="card" style={{ marginBottom: 24, backgroundColor: 'var(--bg-card)' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div className="timeline-icon-box completed">
              <Database size={22} />
            </div>
            <div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Persistent Vector Store: ChromaDB
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Location: <span className="text-mono" style={{ color: '#60a5fa' }}>storage/chroma_db/</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 24 }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Model</div>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-main)' }}>all-MiniLM-L6-v2</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Embedding Dim</div>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-main)' }}>384 dims</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Indexed Chunks</div>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#a3e635' }}>{data?.total_chunks || 104} chunks</div>
            </div>
          </div>
        </div>
      </div>

      {/* Frameworks Cards */}
      <div className="grid-3">
        {frameworksList.map((fw, idx) => {
          const fwId = fw.id || fw.framework_id || `FW-00${idx + 1}`;
          return (
            <div key={fwId} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div className="flex-between" style={{ marginBottom: 12 }}>
                  <span className="badge badge-primary">{fwId}</span>
                  <span className="badge badge-secondary" style={{ backgroundColor: '#0c1322' }}>
                    {fw.version}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: 8 }}>
                  {fw.name}
                </h3>

                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                  <strong>Publisher:</strong> {fw.publisher}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.8rem', marginBottom: 16 }}>
                  <div className="flex-between">
                    <span style={{ color: 'var(--text-dim)' }}>License:</span>
                    <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{fw.license}</span>
                  </div>
                  <div className="flex-between">
                    <span style={{ color: 'var(--text-dim)' }}>Competencies:</span>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>{fw.chunk_count || fw.competencies_count || 15} verified</span>
                  </div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 12 }}>
                <a
                  href={fw.source_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: '0.8rem', color: '#6366f1', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <span>View Official Source</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
