"""Renders the article's exhibits as 300 dpi PNGs. Values are copied from the release reports in this repo."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
INK, MUTED, RULE, HEAD, SHADE, WHITE = (26, 29, 39), (107, 114, 128), (210, 214, 222), (238, 240, 245), (199, 210, 254), (255, 255, 255)


def _font(path, size):
    return ImageFont.truetype(path, size)


def table_png(path, title, headers, rows, assumption, shade=None, width=2400):
    title_f, head_f, body_f, note_f = _font(BOLD, 52), _font(BOLD, 40), _font(REG, 38), _font(REG, 32)
    pad, row_h = 60, 96
    col_w = []
    for i, h in enumerate(headers):
        longest = max([len(h)] + [len(str(r[i])) for r in rows])
        col_w.append(longest)
    total = sum(col_w)
    widths = [int((width - 2 * pad) * c / total) for c in col_w]
    lines = [title]
    height = pad + 110 + row_h * (len(rows) + 1) + 120 + 60 * (len(assumption) // 110 + 1) + pad
    img = Image.new("RGB", (width, height), WHITE)
    d = ImageDraw.Draw(img)
    y = pad
    d.text((pad, y), title, font=title_f, fill=INK)
    y += 110
    x0 = pad
    d.rectangle([pad, y, width - pad, y + row_h], fill=HEAD)
    x = pad
    for w, h in zip(widths, headers):
        d.text((x + 20, y + 26), h, font=head_f, fill=INK)
        x += w
    y += row_h
    for r_i, row in enumerate(rows):
        x = pad
        for c_i, (w, val) in enumerate(zip(widths, row)):
            fill = SHADE if shade == (r_i, c_i) else None
            if fill:
                d.rectangle([x, y, x + w, y + row_h], fill=fill)
            d.text((x + 20, y + 26), str(val), font=body_f, fill=INK)
            x += w
        d.line([pad, y + row_h, width - pad, y + row_h], fill=RULE, width=2)
        y += row_h
    y += 30
    words, line, out = assumption.split(), "", []
    for w in words:
        if len(line) + len(w) > 105:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    out.append(line)
    for ln in out:
        d.text((pad, y), ln, font=note_f, fill=MUTED)
        y += 44
    img = img.crop((0, 0, width, y + pad))
    img.save(path, dpi=(300, 300))


def flow_png(path, width=2400, height=1000):
    img = Image.new("RGB", (width, height), WHITE)
    d = ImageDraw.Draw(img)
    f_title, f_box, f_small = _font(BOLD, 50), _font(BOLD, 40), _font(REG, 32)
    d.text((60, 40), "One manifest, one generated agent, one gate", font=f_title, fill=INK)
    boxes = [
        ("Manifest", "owner, tool grants,\nbudget, approval rule,\ngate thresholds"),
        ("Generator", "renders the agent\nand scenario from\nthe manifest"),
        ("Harness run", "grants, budget and approval\nenforced; intent note;\nguard escalates unactioned refunds"),
        ("Eval and gate", "36 cases; pass rate and\ncritical violations\nagainst the manifest"),
        ("Release report", "pass counts, tokens,\nescalations, cost per\nsuccessful outcome"),
    ]
    bw, gap, top, bh = 400, 60, 260, 380
    x = 60
    for i, (name, body) in enumerate(boxes):
        d.rounded_rectangle([x, top, x + bw, top + bh], radius=24, outline=INK, width=4, fill=HEAD)
        d.text((x + 30, top + 30), name, font=f_box, fill=INK)
        for k, ln in enumerate(body.split("\n")):
            d.text((x + 30, top + 130 + k * 60), ln, font=f_small, fill=INK)
        if i < len(boxes) - 1:
            ax = x + bw + 8
            d.line([ax, top + bh // 2, ax + gap - 16, top + bh // 2], fill=INK, width=5)
            d.polygon([(ax + gap - 16, top + bh // 2 - 14), (ax + gap - 16, top + bh // 2 + 14),
                       (ax + gap, top + bh // 2)], fill=INK)
        x += bw + gap
    d.text((60, 740), "Measured: pass/fail per case, tool, status, tokens, escalations, violations, timings.", font=f_small, fill=INK)
    d.text((60, 790), "Assumed: review minutes and hourly rate, token price, remediation cost. Each has no default.", font=f_small, fill=INK)
    d.text((60, 840), "Scripted in the scenario: the intent note and the guard. The model still chooses the tool.", font=f_small, fill=INK)
    img.save(path, dpi=(300, 300))


if __name__ == "__main__":
    table_png(HERE / "exhibit-1-progression.png",
              "Exhibit 1. Intent context moved refund-desk from 5 of 8 to 8 of 8",
              ["Run", "ticket-triage", "case-notes", "refund-desk", "support-agent"],
              [["1  unscoped prompt", "7/7", "3/5", "5/8", "13/16"],
               ["2  scoped prompt", "7/7", "5/5", "5/8", "13/16"],
               ["3  + guard", "7/7", "5/5", "5/8", "13/16"],
               ["4  + intent context", "7/7", "5/5", "8/8", "15/16"],
               ["5  + owner decision on policy_lookup", "7/7", "5/5", "8/8", "16/16"]],
              "Assumptions: none. Counts are cases passed on gpt-oss-120b, one run each. Run 5 changes one expected action (policy_lookup) by owner decision. Source: release-run1 to release-run4 summaries, release.json.",
              shade=(4, 3))
    table_png(HERE / "exhibit-2-economics.png",
              "Exhibit 2. Human review, not tokens, sets the cost per successful outcome",
              ["Agent", "Tokens", "Token cost", "Escalations", "Review cost", "Successful", "Cost per success"],
              [["ticket-triage", "2,543", "$0.0127", "1", "$7.08", "7", "$1.01"],
               ["case-notes", "1,705", "$0.0085", "0", "$0.00", "5", "$0.00"],
               ["refund-desk", "8,399", "$0.0420", "5", "$35.42", "8", "$4.43"],
               ["support-agent", "12,165", "$0.0608", "5", "$35.42", "16", "$2.22"],
               ["All four", "24,812", "$0.1241", "11", "$77.92", "36", "$2.17"]],
              "Assumptions: $0.005 per 1,000 tokens; 5 minutes of review per escalation at $85 an hour; remediation $970 per violation (none occurred). Tokens and escalations measured; prices are assumed. Source: release.json (gpt-oss-120b).",
              shade=(2, 6))
    table_png(HERE / "exhibit-3-models.png",
              "Exhibit 3. Two models made the same decision on all 36 cases",
              ["Agent", "Cases gpt-oss", "Cases qwen3", "Tokens gpt-oss", "Tokens qwen3", "Same decision"],
              [["ticket-triage", "7/7", "7/7", "2,543", "2,862", "7/7"],
               ["case-notes", "5/5", "5/5", "1,705", "1,895", "5/5"],
               ["refund-desk", "8/8", "8/8", "8,399", "8,831", "8/8"],
               ["support-agent", "16/16", "16/16", "12,165", "13,062", "16/16"],
               ["All four", "36/36", "36/36", "24,812", "26,650", "36/36"]],
              "Same decision = same tool and same final status on every case. One run per model. Token counts from each API's usage field. Source: release.json and runs/qwen3-32b/release.json.")
    flow_png(HERE / "figure-factory-flow.png")
    print("rendered")
