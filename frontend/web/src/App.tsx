// App.tsx
// Main FEA Platform interface

import { useState } from 'react';
import axios from 'axios';

// API base URL - FastAPI runs on port 8000
const API = 'http://localhost:8000';

// TypeScript interfaces - define the shape of our data
interface Material {
  name: string;
  E: number;
  nu: number;
  rho: number;
  fy: number;
}

interface AnalysisResult {
  status: string;
  num_nodes: number;
  num_elements: number;
  max_displacement: number;
  max_von_mises: number;
  safety_factor: number;
  assessment: string;
}

function App() {

  // State variables - React re-renders when these change
  const [file, setFile]           = useState<File | null>(null);
  const [fileId, setFileId]       = useState<string>('');
  const [materials, setMaterials] = useState<Material[]>([]);
  const [selMat, setSelMat]       = useState<Material | null>(null);
  const [forceZ, setForceZ]       = useState<number>(-10000);
  const [meshSize, setMeshSize]   = useState<number>(8);
  const [status, setStatus]       = useState<string>('');
  const [loading, setLoading]     = useState<boolean>(false);
  const [results, setResults]     = useState<AnalysisResult | null>(null);

  // Load materials from API when component mounts
  const loadMaterials = async () => {
    try {
      const res = await axios.get(`${API}/materials`);
      setMaterials(res.data.materials);
      setSelMat(res.data.materials[0]);
    } catch {
      setStatus('Could not load materials from API. Is FastAPI running?');
    }
  };

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setFileId('');
      setResults(null);
      setStatus(`File selected: ${f.name}`);
    }
  };

  // Upload file to FastAPI
  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setStatus('Uploading file...');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await axios.post(`${API}/upload`, form);
      setFileId(res.data.file_id);
      setStatus(`✓ Uploaded: ${res.data.filename} (${res.data.size_kb} KB)`);
      if (materials.length === 0) await loadMaterials();
    } catch (err: any) {
      setStatus(`Upload failed: ${err.message}`);
    }
    setLoading(false);
  };

  // Run FEA analysis
  const handleAnalyze = async () => {
    if (!fileId || !selMat) return;
    setLoading(true);
    setResults(null);
    setStatus('Running FEA analysis... this may take 30-60 seconds');
    try {
      const res = await axios.post(`${API}/analyze`, {
        file_id  : fileId,
        material : {
          name           : selMat.name,
          youngs_modulus : selMat.E,
          poisson_ratio  : selMat.nu,
          density        : selMat.rho,
          yield_strength : selMat.fy,
        },
        force_z   : forceZ,
        mesh_size : meshSize,
      });
      setResults(res.data);
      setStatus('✓ Analysis complete');
    } catch (err: any) {
      setStatus(`Analysis failed: ${err.response?.data?.detail || err.message}`);
    }
    setLoading(false);
  };

  // Safety factor color
  const sfColor = (sf: number) => {
    if (sf >= 2.0) return '#22c55e';  // green
    if (sf >= 1.0) return '#f59e0b';  // yellow
    return '#ef4444';                  // red
  };

  return (
    <div style={styles.container}>

      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>⚙ FEA Platform</h1>
        <p style={styles.subtitle}>Finite Element Analysis — Linear Static</p>
      </div>

      <div style={styles.main}>

        {/* Left panel */}
        <div style={styles.panel}>

          {/* Step 1: Upload */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>1 — Upload STEP File</h2>
            <input
              type="file"
              accept=".step,.stp"
              onChange={handleFileSelect}
              style={styles.fileInput}
            />
            {file && (
              <button
                onClick={handleUpload}
                disabled={loading}
                style={styles.btn}
              >
                {loading ? 'Uploading...' : 'Upload File'}
              </button>
            )}
          </div>

          {/* Step 2: Material */}
          {fileId && (
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>2 — Select Material</h2>
              {materials.length === 0 ? (
                <button onClick={loadMaterials} style={styles.btn}>Load Materials</button>
              ) : (
                <select
                  onChange={e => setSelMat(materials[parseInt(e.target.value)])}
                  style={styles.select}
                >
                  {materials.map((m, i) => (
                    <option key={i} value={i}>{m.name}</option>
                  ))}
                </select>
              )}
              {selMat && (
                <div style={styles.matProps}>
                  <span>E = {selMat.E.toLocaleString()} MPa</span>
                  <span>ν = {selMat.nu}</span>
                  <span>fy = {selMat.fy} MPa</span>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Loads */}
          {fileId && (
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>3 — Define Loads</h2>
              <label style={styles.label}>
                Force Z (N) — negative = downward
              </label>
              <input
                type="number"
                value={forceZ}
                onChange={e => setForceZ(parseFloat(e.target.value))}
                style={styles.input}
              />
              <label style={styles.label}>Mesh Size (mm)</label>
              <input
                type="number"
                value={meshSize}
                min={2} max={20}
                onChange={e => setMeshSize(parseFloat(e.target.value))}
                style={styles.input}
              />
              <button
                onClick={handleAnalyze}
                disabled={loading}
                style={{...styles.btn, ...styles.btnAnalyze}}
              >
                {loading ? '⏳ Analyzing...' : '▶ Run Analysis'}
              </button>
            </div>
          )}

          {/* Status */}
          {status && (
            <div style={styles.status}>{status}</div>
          )}
        </div>

        {/* Right panel - Results */}
        <div style={styles.panel}>
          {results ? (
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>Analysis Results</h2>

              <div style={styles.resultGrid}>
                <div style={styles.resultItem}>
                  <span style={styles.resultLabel}>Nodes</span>
                  <span style={styles.resultValue}>{results.num_nodes.toLocaleString()}</span>
                </div>
                <div style={styles.resultItem}>
                  <span style={styles.resultLabel}>Elements</span>
                  <span style={styles.resultValue}>{results.num_elements.toLocaleString()}</span>
                </div>
                <div style={styles.resultItem}>
                  <span style={styles.resultLabel}>Max Displacement</span>
                  <span style={styles.resultValue}>{results.max_displacement.toFixed(4)} mm</span>
                </div>
                <div style={styles.resultItem}>
                  <span style={styles.resultLabel}>Max Von Mises</span>
                  <span style={styles.resultValue}>{results.max_von_mises.toFixed(2)} MPa</span>
                </div>
              </div>

              {/* Safety factor */}
              <div style={{...styles.sfBox, borderColor: sfColor(results.safety_factor)}}>
                <span style={styles.sfLabel}>Safety Factor</span>
                <span style={{...styles.sfValue, color: sfColor(results.safety_factor)}}>
                  {results.safety_factor.toFixed(2)}
                </span>
                <span style={styles.sfAssessment}>{results.assessment}</span>
              </div>
            </div>
          ) : (
            <div style={styles.placeholder}>
              <p>Upload a STEP file and run analysis to see results here.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  container   : { minHeight: '100vh', background: 'linear-gradient(135deg, #0a0f1e 0%, #0d1b3e 100%)', color: '#e2e8f0', fontFamily: "'Segoe UI', system-ui, sans-serif" },
  header      : { padding: '40px 48px 32px', textAlign: 'center', borderBottom: '1px solid rgba(56,189,248,0.15)', background: 'rgba(56,189,248,0.03)' },
  title       : { margin: 0, fontSize: 42, fontWeight: 800, color: '#38bdf8', letterSpacing: '-1px', textShadow: '0 0 40px rgba(56,189,248,0.4)' },
  subtitle    : { margin: '8px 0 0', color: '#64748b', fontSize: 15, letterSpacing: '2px', textTransform: 'uppercase' as const },
  main        : { display: 'flex', gap: 28, padding: '36px 48px' },
  panel       : { flex: 1, display: 'flex', flexDirection: 'column' as const, gap: 20 },
  card        : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(56,189,248,0.12)', backdropFilter: 'blur(10px)', borderRadius: 16, padding: 24 },
  cardTitle   : { margin: '0 0 18px', fontSize: 13, color: '#38bdf8', letterSpacing: '2px', textTransform: 'uppercase' as const, fontWeight: 600 },
  fileInput   : { width: '100%', marginBottom: 14, color: '#94a3b8', fontSize: 13 },
  btn         : { width: '100%', padding: '11px 0', background: 'linear-gradient(90deg, #0284c7, #0369a1)', color: '#fff', border: 'none', borderRadius: 10, cursor: 'pointer', fontSize: 14, fontWeight: 600, letterSpacing: '0.5px', transition: 'opacity 0.2s' },
  btnAnalyze  : { background: 'linear-gradient(90deg, #16a34a, #15803d)', fontSize: 15, padding: '14px 0', marginTop: 8, boxShadow: '0 4px 20px rgba(22,163,74,0.3)' },
  select      : { width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', color: '#e2e8f0', border: '1px solid rgba(56,189,248,0.2)', borderRadius: 10, marginBottom: 14, fontSize: 14 },
  label       : { display: 'block', fontSize: 11, color: '#64748b', marginBottom: 6, letterSpacing: '1px', textTransform: 'uppercase' as const },
  input       : { width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', color: '#e2e8f0', border: '1px solid rgba(56,189,248,0.2)', borderRadius: 10, marginBottom: 14, boxSizing: 'border-box' as const, fontSize: 14 },
  matProps    : { display: 'flex', gap: 16, flexWrap: 'wrap' as const, fontSize: 12, color: '#64748b', marginTop: 10, padding: '10px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 8 },
  status      : { background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: 10, padding: '12px 16px', fontSize: 13, color: '#94a3b8' },
  placeholder : { background: 'rgba(255,255,255,0.02)', border: '2px dashed rgba(56,189,248,0.15)', borderRadius: 16, padding: 60, textAlign: 'center' as const, color: '#334155', fontSize: 15 },
  resultGrid  : { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 20 },
  resultItem  : { background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12, padding: 16 },
  resultLabel : { display: 'block', fontSize: 11, color: '#64748b', marginBottom: 6, letterSpacing: '1px', textTransform: 'uppercase' as const },
  resultValue : { fontSize: 22, fontWeight: 700, color: '#f1f5f9' },
  sfBox       : { border: '2px solid', borderRadius: 16, padding: 28, textAlign: 'center' as const, background: 'rgba(0,0,0,0.2)' },
  sfLabel     : { display: 'block', fontSize: 11, color: '#64748b', marginBottom: 10, letterSpacing: '2px', textTransform: 'uppercase' as const },
  sfValue     : { display: 'block', fontSize: 64, fontWeight: 800, marginBottom: 10, letterSpacing: '-2px' },
  sfAssessment: { fontSize: 14, color: '#94a3b8', lineHeight: 1.5 },
};
export default App;