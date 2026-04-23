import React from 'react';
// Bento.jsx — bento feature grid
const Bento = () => {
  return (
    <section id="platform" className="section page">
      <div className="section-head">
        <div>
          <span className="eyebrow">Platform</span>
          <h2 style={{ marginTop: 16 }}>
            One console.<br/>
            <span className="grad-text">Every marketing motion.</span>
          </h2>
        </div>
        <p>
          A bento of tightly-scoped agents and primitives — each one evaluable, swappable, and
          wired into the same observability spine.
        </p>
      </div>

      <div className="bento">
        {/* 1. Big RAG + knowledge hero */}
        <div className="bento-cell cell-dark col-7 row-2" style={{ minHeight: 340 }}>
          <div className="cell-glow" style={{ top: -120, right: -80, background: 'radial-gradient(circle, rgba(99,102,241,0.45), transparent 65%)' }} />
          <div className="cell-glow" style={{ bottom: -140, left: -80, background: 'radial-gradient(circle, rgba(236,72,153,0.3), transparent 65%)' }} />
          <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
            <span className="eyebrow eyebrow-dark">RAG · Brand grounded</span>
            <h3 className="cell-title" style={{ fontSize: 30, maxWidth: 440 }}>
              Answers pulled from <span className="grad-text">your</span> knowledge base, not the open web.
            </h3>
            <p className="cell-sub" style={{ maxWidth: 460 }}>
              Drop in brand guidelines, personas, product catalogs, and historical benchmarks.
              Agents cite the exact document chunk that grounded each decision.
            </p>
            <div style={{ flex: 1 }} />
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 24 }}>
              <span className="chip chip-indigo">49 documents</span>
              <span className="chip chip-slate" style={{ background: 'rgba(255,255,255,0.06)', color: '#C7D2FE', borderColor: 'rgba(255,255,255,0.12)' }}>4 personas</span>
              <span className="chip chip-slate" style={{ background: 'rgba(255,255,255,0.06)', color: '#C7D2FE', borderColor: 'rgba(255,255,255,0.12)' }}>10 industries</span>
              <span className="chip chip-slate" style={{ background: 'rgba(255,255,255,0.06)', color: '#C7D2FE', borderColor: 'rgba(255,255,255,0.12)' }}>40 DMAs</span>
            </div>
          </div>
        </div>

        {/* 2. Observability gradient card */}
        <div className="bento-cell cell-grad col-5" style={{ minHeight: 160 }}>
          <div className="cell-glow" style={{ top: -100, right: -60, background: 'radial-gradient(circle, rgba(255,255,255,0.22), transparent 65%)' }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <span className="label-xs" style={{ color: 'rgba(255,255,255,0.85)' }}>Observability</span>
            <h3 className="cell-title">Every turn, every token, every tool call.</h3>
            <p style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14, lineHeight: 1.5 }}>
              Langfuse-backed tracing shows the full agentic loop live — debug in seconds, not hours.
            </p>
          </div>
        </div>

        {/* 3. Eval harness */}
        <div className="bento-cell col-5" style={{ minHeight: 160 }}>
          <div className="icon-tile it-emerald">E</div>
          <h3 className="cell-title">Eval harness you can trust</h3>
          <p className="cell-sub">
            57 golden examples, deterministic + LLM-as-judge metrics, automatic regression
            detection when any metric drops more than 5%.
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
            <span className="chip chip-emerald">100% pass rate</span>
            <span className="chip chip-slate">$0.05 per run</span>
          </div>
        </div>

        {/* 4. A/B Testing */}
        <div className="bento-cell col-4" style={{ minHeight: 220 }}>
          <div className="icon-tile it-amber">A</div>
          <h3 className="cell-title">Statistically valid A/B</h3>
          <p className="cell-sub">Stratified sampling across industry × size × DMA × ad experience. Power analysis built in.</p>
          <div style={{ marginTop: 16, padding: 12, background: 'var(--canvas)', borderRadius: 12, border: '1px solid var(--line)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', fontWeight: 700 }}>
              <span>POWER</span><span>0.82</span>
            </div>
            <div style={{ height: 6, background: 'var(--line-soft)', borderRadius: 4, marginTop: 6, overflow: 'hidden' }}>
              <div style={{ width: '82%', height: '100%', background: 'linear-gradient(90deg, #F59E0B, #EF4444)' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', fontWeight: 700, marginTop: 10 }}>
              <span>SAMPLE / ARM</span><span>n = 1,248</span>
            </div>
          </div>
        </div>

        {/* 5. Brand safety */}
        <div className="bento-cell col-4" style={{ minHeight: 220 }}>
          <div className="icon-tile it-pink">B</div>
          <h3 className="cell-title">Brand safety, by default</h3>
          <p className="cell-sub">Every creative passes a phrase allowlist, claim validator, and tone check before it ever ships to review.</p>
          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
              <div className="bullet-check">✓</div>
              <span style={{ fontWeight: 600 }}>Prohibited phrases</span>
              <span className="sp" />
              <span style={{ color: 'var(--emerald)', fontWeight: 700 }}>0 flagged</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
              <div className="bullet-check">✓</div>
              <span style={{ fontWeight: 600 }}>Unsubstantiated claims</span>
              <span className="sp" />
              <span style={{ color: 'var(--emerald)', fontWeight: 700 }}>0 flagged</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
              <div className="bullet-check">✓</div>
              <span style={{ fontWeight: 600 }}>Voice & tone</span>
              <span className="sp" />
              <span style={{ color: 'var(--emerald)', fontWeight: 700 }}>4.6 / 5</span>
            </div>
          </div>
        </div>

        {/* 6. Brand swappable */}
        <div className="bento-cell col-4" style={{ minHeight: 220, background: '#0A0A0A', borderColor: 'transparent', color: 'white' }}>
          <span className="eyebrow eyebrow-dark">Swappable brands</span>
          <h3 className="cell-title" style={{ color: 'white' }}>One env var.<br/>Any brand.</h3>
          <p style={{ color: '#A1A1AA', fontSize: 14, lineHeight: 1.5, marginTop: 8 }}>
            Agents read from the active brand config at runtime. Add a folder, set ACTIVE_BRAND, re-ingest.
          </p>
          <div style={{ marginTop: 16, fontFamily: 'SF Mono, ui-monospace, monospace', fontSize: 11, background: 'rgba(255,255,255,0.06)', padding: 10, borderRadius: 10, color: '#E4E4E7' }}>
            <div><span style={{ color: '#A1A1AA' }}># .env</span></div>
            <div>ACTIVE_BRAND=<span style={{ color: '#A5B4FC', fontWeight: 700 }}>meta</span></div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Bento;
