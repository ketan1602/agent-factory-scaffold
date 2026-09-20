from __future__ import annotations


def time_comparison_chart() -> str:
    """Two-bar SVG chart comparing factory vs handcrafted agent creation time."""
    factory_minutes = 28
    handcrafted_minutes = 4320
    max_val = handcrafted_minutes
    bar_w = 80
    chart_h = 300
    scale = (chart_h - 60) / max_val

    factory_h = max(int(factory_minutes * scale), 4)
    handcrafted_h = int(handcrafted_minutes * scale)
    factory_y = chart_h - 40 - factory_h
    handcrafted_y = chart_h - 40 - handcrafted_h

    return f"""<svg viewBox="0 0 400 {chart_h + 60}" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{ fill: #e2e8f0; font-family: system-ui, sans-serif; font-size: 12px; }}
    .label {{ font-size: 11px; fill: #6b7280; }}
    .value {{ font-weight: bold; fill: #e2e8f0; font-size: 13px; }}
    .title {{ font-size: 14px; font-weight: bold; fill: #e2e8f0; }}
  </style>
  <rect width="400" height="{chart_h + 60}" fill="#1a1d27" rx="8"/>
  <text x="200" y="28" text-anchor="middle" class="title">Time to Production-Ready Agent</text>
  <rect x="60" y="{factory_y}" width="{bar_w}" height="{factory_h}" fill="#6366f1" rx="4"/>
  <rect x="220" y="{handcrafted_y}" width="{bar_w}" height="{handcrafted_h}" fill="#6b7280" rx="4"/>
  <text x="100" y="{factory_y - 6}" text-anchor="middle" class="value">28 min</text>
  <text x="260" y="{handcrafted_y - 6}" text-anchor="middle" class="value">4,320 min</text>
  <line x1="40" y1="{chart_h - 40}" x2="360" y2="{chart_h - 40}" stroke="#2a2d3a" stroke-width="1"/>
  <text x="100" y="{chart_h - 20}" text-anchor="middle" class="label">Factory</text>
  <text x="260" y="{chart_h - 20}" text-anchor="middle" class="label">Handcrafted (3 days)</text>
</svg>"""


def decisions_chart() -> str:
    """Two-bar SVG chart comparing decisions with vs without factory."""
    with_factory = 3
    without_factory = 35
    max_val = without_factory
    bar_w = 80
    chart_h = 300
    scale = (chart_h - 60) / max_val

    with_h = max(int(with_factory * scale), 4)
    without_h = int(without_factory * scale)
    with_y = chart_h - 40 - with_h
    without_y = chart_h - 40 - without_h

    return f"""<svg viewBox="0 0 400 {chart_h + 60}" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{ fill: #e2e8f0; font-family: system-ui, sans-serif; font-size: 12px; }}
    .label {{ font-size: 11px; fill: #6b7280; }}
    .value {{ font-weight: bold; fill: #e2e8f0; font-size: 13px; }}
    .title {{ font-size: 14px; font-weight: bold; fill: #e2e8f0; }}
  </style>
  <rect width="400" height="{chart_h + 60}" fill="#1a1d27" rx="8"/>
  <text x="200" y="28" text-anchor="middle" class="title">Engineering Decisions Required</text>
  <rect x="60" y="{with_y}" width="{bar_w}" height="{with_h}" fill="#22c55e" rx="4"/>
  <rect x="220" y="{without_y}" width="{bar_w}" height="{without_h}" fill="#6b7280" rx="4"/>
  <text x="100" y="{with_y - 6}" text-anchor="middle" class="value">3</text>
  <text x="260" y="{without_y - 6}" text-anchor="middle" class="value">35</text>
  <line x1="40" y1="{chart_h - 40}" x2="360" y2="{chart_h - 40}" stroke="#2a2d3a" stroke-width="1"/>
  <text x="100" y="{chart_h - 20}" text-anchor="middle" class="label">With Factory</text>
  <text x="260" y="{chart_h - 20}" text-anchor="middle" class="label">Without Factory</text>
</svg>"""
