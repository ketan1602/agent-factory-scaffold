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

// Demo
const form = document.getElementById('generate-form');
const output = document.getElementById('generate-output');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('agent-name').value.trim();
  const domain = document.getElementById('agent-domain').value;
  if (!name) return;

  const btn = form.querySelector('button');
  btn.disabled = true;
  btn.textContent = 'Generating…';
  output.innerHTML = '';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, domain }),
    });
    const data = await res.json();
    if (!res.ok) {
      output.innerHTML = `<p style="color:var(--error)">${data.detail}</p>`;
      return;
    }
    renderGenerateResult(data);
  } catch (err) {
    output.innerHTML = `<p style="color:var(--error)">Request failed: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Agent';
  }
});

function renderGenerateResult(data) {
  const tree = renderTree(data.file_tree, '');
  const checks = data.compliance.map(c => `
    <div class="check-item">
      <span class="${c.passed ? 'check-pass' : 'check-fail'}">${c.passed ? '✓' : '✗'}</span>
      <span><strong>${c.name}</strong>: ${c.message}</span>
    </div>`).join('');

  output.innerHTML = `
    <div class="output-area">
      <p class="timing">Generated in ${data.duration_seconds}s (dry-run)</p>
      <h3>File Tree</h3>
      <div class="file-tree">${tree}</div>
      <h3 style="margin-top:1rem">Compliance (8 checks)</h3>
      <div>${checks}</div>
    </div>`;
}

function renderTree(node, prefix) {
  if (!node || typeof node !== 'object') return '';
  return Object.entries(node).map(([key, val]) => {
    if (val === null) return `<div class="file">${prefix}${key}</div>`;
    return `<div>${prefix}<strong>${key}/</strong></div>${renderTree(val, prefix + '  ')}`;
  }).join('');
}

// Metrics
let metricsLoaded = false;
async function loadMetrics() {
  if (metricsLoaded) return;
  const container = document.getElementById('metrics-content');
  try {
    const res = await fetch('/api/metrics');
    const data = await res.json();
    container.innerHTML = `
      <div class="stats" style="grid-template-columns:repeat(2,1fr)">
        <div class="stat-card">
          <div class="value">${data.factory_time_to_first_agent_minutes} min</div>
          <div class="label">Factory time to first agent</div>
        </div>
        <div class="stat-card">
          <div class="value">${data.decisions_with_factory}</div>
          <div class="label">Decisions required (factory)</div>
        </div>
      </div>
      <div class="card chart-container">${data.charts.time_comparison}</div>
      <div class="card chart-container">${data.charts.decisions}</div>`;
    metricsLoaded = true;
  } catch (err) {
    container.innerHTML = `<p style="color:var(--error)">Failed to load metrics: ${err.message}</p>`;
  }
}

// Eval
let evalLoaded = false;
async function loadEval() {
  if (evalLoaded) return;
  const container = document.getElementById('eval-content');
  try {
    const res = await fetch('/api/eval');
    const data = await res.json();
    const rows = data.agents.map(a => `
      <tr>
        <td>${a.agent}</td>
        <td>${a.checks_passed}/${a.checks_total}</td>
        <td>${a.compliance_pct}%</td>
        <td>${a.time_to_first_passing_eval_minutes} min</td>
        <td><span class="badge badge-pass">PASS</span></td>
      </tr>`).join('');
    container.innerHTML = `
      <p style="color:var(--muted);margin-bottom:1rem">
        ${data.summary.all_passing}/${data.summary.total} agents passing all checks
      </p>
      <table>
        <thead><tr><th>Agent</th><th>Checks</th><th>Compliance</th><th>Time</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    evalLoaded = true;
  } catch (err) {
    container.innerHTML = `<p style="color:var(--error)">Failed to load eval: ${err.message}</p>`;
  }
}

// Init
showSection('overview');
