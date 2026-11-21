from __future__ import annotations

_STYLE = """<style>
    text { fill: #e2e8f0; font-family: system-ui, sans-serif; font-size: 12px; }
    .label { font-size: 11px; fill: #6b7280; }
    .value { font-weight: bold; font-size: 13px; }
  </style>"""


def time_chart(minutes: float) -> str:
    """One measured bar: minutes from generate to the end of the live eval."""
    bar_max = 300
    width = max(min(minutes / 10 * bar_max, bar_max), 4)
    return f"""<svg viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">{_STYLE}
  <rect width="400" height="140" fill="#1a1d27" rx="8"/>
  <text x="50" y="40" class="label">Generate + live eval (measured)</text>
  <rect x="50" y="60" width="{width:.0f}" height="28" fill="#6366f1" rx="4"/>
  <text x="50" y="112" class="value">{minutes:.2f} min</text>
</svg>"""


def pass_chart(passed: int, total: int) -> str:
    """Measured share of eval cases that passed."""
    bar_max = 300
    share = passed / total if total else 0.0
    return f"""<svg viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">{_STYLE}
  <rect width="400" height="140" fill="#1a1d27" rx="8"/>
  <text x="50" y="40" class="label">Eval cases passed (measured)</text>
  <rect x="50" y="60" width="{bar_max}" height="28" fill="#2a2d3a" rx="4"/>
  <rect x="50" y="60" width="{share * bar_max:.0f}" height="28" fill="#22c55e" rx="4"/>
  <text x="50" y="112" class="value">{passed}/{total}</text>
</svg>"""
