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

// Overview: the same measured numbers as Metrics
async function loadOverview() {
  const res = await fetch('/api/metrics');
  const data = await res.json();
  if (!data.available) return;
  document.getElementById('stat-time').textContent = `${data.time_to_eval_minutes} min`;
  document.getElementById('stat-cases').textContent = `${data.cases_passed}/${data.cases_total}`;
  document.getElementById('stat-compliance').textContent =
    `${data.compliance_checks_passed}/${data.compliance_checks_total}`;
}

// Demo
const form = document.getElementById('generate-form');
const output = document.getElementById('generate-output');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('agent-name').value.trim();
  if (!name) return;

  const btn = form.querySelector('button');
  btn.disabled = true;
  btn.textContent = 'Working…';
  output.innerHTML = '';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
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
    btn.textContent = 'Preview Files';
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
      <p class="timing">Rendered in ${data.duration_seconds}s (dry-run, nothing written)</p>
      <h3>File Tree</h3>
      <div class="file-tree">${tree}</div>
      <h3 style="margin-top:1rem">Compliance of ${data.compliance_source}</h3>
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
    if (!data.available) {
      container.innerHTML = `<p style="color:var(--muted)">${data.message}</p>`;
      return;
    }
    container.innerHTML = `
      <p style="color:var(--muted);margin-bottom:1rem">
        Model: <code>${data.model}</code> · measured ${data.measured_at}
      </p>
      <div class="stats" style="grid-template-columns:repeat(3,1fr)">
        <div class="stat-card"><div class="value">${data.generate_seconds}s</div><div class="label">Generate</div></div>
        <div class="stat-card"><div class="value">${data.eval_seconds}s</div><div class="label">Live eval</div></div>
        <div class="stat-card"><div class="value">${data.total_tokens}</div><div class="label">Tokens (model usage)</div></div>
      </div>
      <div class="card chart-container">${data.charts.time_to_eval}</div>
      <div class="card chart-container">${data.charts.cases_passed}</div>`;
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
    if (!data.available) {
      container.innerHTML = `<p style="color:var(--muted)">${data.message}</p>`;
      return;
    }
    const rows = data.results.map(r => `
      <tr>
        <td>${r.case}</td>
        <td>${r.category}</td>
        <td>${r.tool ?? '—'}</td>
        <td>${r.status}</td>
        <td><span class="badge ${r.passed ? 'badge-pass' : 'badge-fail'}">${r.passed ? 'PASS' : 'FAIL'}</span></td>
      </tr>`).join('');
    container.innerHTML = `
      <p style="color:var(--muted);margin-bottom:1rem">
        ${data.cases_passed}/${data.cases_total} cases passed · model <code>${data.model}</code>
      </p>
      <table>
        <thead><tr><th>Case</th><th>Category</th><th>Tool</th><th>Status</th><th>Result</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    evalLoaded = true;
  } catch (err) {
    container.innerHTML = `<p style="color:var(--error)">Failed to load eval: ${err.message}</p>`;
  }
}

// Init
showSection('overview');
loadOverview();
