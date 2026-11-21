// Navigation
const sections = ['overview', 'demo', 'metrics', 'eval'];

function showSection(name) {
  sections.forEach(s => {
    document.getElementById(`section-${s}`).classList.toggle('active', s === name);
    document.getElementById(`nav-${s}`).classList.toggle('active', s === name);
  });
  if (name === 'metrics') loadMetrics();
  if (name === 'eval') loadEval();
}

sections.forEach(s => {
  document.getElementById(`nav-${s}`).addEventListener('click', () => showSection(s));
});

const esc = (v) => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = (v) => (v === null || v === undefined) ? 'n/a' : `$${Number(v).toFixed(4)}`;

// Overview
async function loadOverview() {
  const data = await (await fetch('/api/metrics')).json();
  if (!data.available) return;
  document.getElementById('stat-released').textContent =
    `${data.summary.agents_released}/${data.summary.agents_total}`;
  document.getElementById('stat-cases').textContent =
    `${data.summary.cases_passed}/${data.summary.cases_total}`;
  document.getElementById('stat-cost').textContent = money(data.summary.cost_per_successful_outcome_usd);
}

// Demo
const form = document.getElementById('generate-form');
const output = document.getElementById('generate-output');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const manifest = document.getElementById('manifest-name').value;
  const btn = form.querySelector('button');
  btn.disabled = true;
  btn.textContent = 'Working…';
  output.innerHTML = '';
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ manifest }),
    });
    const data = await res.json();
    if (!res.ok) {
      output.innerHTML = `<p style="color:var(--error)">${esc(data.detail)}</p>`;
      return;
    }
    renderGenerateResult(data);
  } catch (err) {
    output.innerHTML = `<p style="color:var(--error)">Request failed: ${esc(err.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Preview Files';
  }
});

function renderGenerateResult(data) {
  const tree = renderTree(data.file_tree, '');
  const checks = data.compliance.map(c => `
    <div class="check-item">
      <span class="${c.passed ? 'check-pass' : 'check-fail'}">${c.passed ? '✓' : '✗'}</span>
      <span><strong>${esc(c.name)}</strong>: ${esc(c.message)}</span>
    </div>`).join('');
  output.innerHTML = `
    <div class="output-area">
      <p class="timing">Rendered in ${data.duration_seconds}s (dry-run, nothing written)</p>
      <h3>File Tree</h3>
      <div class="file-tree">${tree}</div>
      <h3 style="margin-top:1rem">Compliance of ${esc(data.compliance_source)}</h3>
      <div>${checks}</div>
    </div>`;
}

function renderTree(node, prefix) {
  if (!node || typeof node !== 'object') return '';
  return Object.entries(node).map(([key, val]) => {
    if (val === null) return `<div class="file">${prefix}${esc(key)}</div>`;
    return `<div>${prefix}<strong>${esc(key)}/</strong></div>${renderTree(val, prefix + '  ')}`;
  }).join('');
}

// Release
let metricsLoaded = false;
async function loadMetrics() {
  if (metricsLoaded) return;
  const container = document.getElementById('metrics-content');
  try {
    const data = await (await fetch('/api/metrics')).json();
    if (!data.available) {
      container.innerHTML = `<p style="color:var(--muted)">${esc(data.message)}</p>`;
      return;
    }
    const rows = data.agents.map(a => `
      <tr>
        <td>${esc(a.agent)}</td>
        <td>${esc(a.owner)}</td>
        <td>${a.cases_passed}/${a.cases_total}</td>
        <td>${a.gate.pass_rate}</td>
        <td>${a.gate.critical_violations}</td>
        <td><span class="badge ${a.gate.blocked ? 'badge-fail' : 'badge-pass'}">${a.gate.blocked ? 'BLOCKED' : 'RELEASED'}</span></td>
        <td>${money(a.economics.cost_per_successful_outcome_usd)}</td>
        <td>${a.compliance_checks_passed}/${a.compliance_checks_total}</td>
      </tr>`).join('');
    container.innerHTML = `
      <p style="color:var(--muted);margin-bottom:1rem">
        Model <code>${esc(data.model)}</code> · measured ${esc(data.measured_at)}
      </p>
      <table>
        <thead><tr><th>Agent</th><th>Owner</th><th>Cases</th><th>Pass rate</th><th>Critical</th><th>Gate</th><th>Cost / success</th><th>Compliance</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="card chart-container" style="margin-top:1rem">${data.charts.cases_passed}</div>`;
    metricsLoaded = true;
  } catch (err) {
    container.innerHTML = `<p style="color:var(--error)">Failed to load release: ${esc(err.message)}</p>`;
  }
}

// Eval
let evalLoaded = false;
async function loadEval() {
  if (evalLoaded) return;
  const container = document.getElementById('eval-content');
  try {
    const data = await (await fetch('/api/eval')).json();
    if (!data.available) {
      container.innerHTML = `<p style="color:var(--muted)">${esc(data.message)}</p>`;
      return;
    }
    container.innerHTML = data.agents.map(a => `
      <div class="card" style="margin-bottom:1rem">
        <h3>${esc(a.agent)} <span style="color:var(--muted);font-size:0.85rem">${a.cases_passed}/${a.cases_total} passed</span></h3>
        <table>
          <thead><tr><th>Case</th><th>Category</th><th>Tool</th><th>Status</th><th>Violated</th><th>Result</th></tr></thead>
          <tbody>${a.results.map(r => `
            <tr>
              <td>${esc(r.case)}</td>
              <td>${esc(r.category)}</td>
              <td>${esc(r.tool ?? '—')}</td>
              <td>${esc(r.status)}</td>
              <td>${r.violated ? 'yes' : 'no'}</td>
              <td><span class="badge ${r.passed ? 'badge-pass' : 'badge-fail'}">${r.passed ? 'PASS' : 'FAIL'}</span></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`).join('');
    evalLoaded = true;
  } catch (err) {
    container.innerHTML = `<p style="color:var(--error)">Failed to load eval: ${esc(err.message)}</p>`;
  }
}

// Init
showSection('overview');
loadOverview();
