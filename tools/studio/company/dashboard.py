"""Static dashboard generation."""

from __future__ import annotations

import html
from pathlib import Path

from .git_info import git_head, git_short_status
from .state import CompanyPaths, load_company_state
from .timeutil import now_iso


def generate_dashboard(root: Path) -> Path:
    paths = CompanyPaths(root)
    data = load_company_state(root)
    state = data["state"]
    gdx = state.get("gdx1", {})
    open_tasks = [task for task in data["tasks"] if task.get("status") not in {"closed", "closed_blocked"}]
    rows = [
        ("Generated", now_iso()),
        ("Git", git_head(root)),
        ("Dirty files", str(len(git_short_status(root)))),
        ("Session", str(state.get("active_session") or "none")),
        ("Open tasks", str(len(open_tasks))),
        ("Locks", str(len(data["locks"]))),
        ("gdx1", f"{gdx.get('network', 'unknown')} / {gdx.get('ssh', 'unknown')}"),
        ("Agents", str(len(data["agents"]))),
    ]
    task_items = "".join(f"<li>{html.escape(task.get('id', ''))}: {html.escape(task.get('status', ''))}</li>" for task in open_tasks) or "<li>none</li>"
    lock_items = "".join(f"<li>{html.escape(lock.get('path', ''))}: {html.escape(lock.get('owner', ''))}</li>" for lock in data["locks"]) or "<li>none</li>"
    stat_cards = "".join(f"<article><b>{html.escape(k)}</b><span>{html.escape(v)}</span></article>" for k, v in rows)
    paths.dashboard_html.parent.mkdir(parents=True, exist_ok=True)
    paths.dashboard_html.write_text(
        f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <link rel=\"icon\" href=\"data:,\">
  <title>Channel Play Studio Dashboard</title>
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; background: #f6f4ef; color: #18212b; }}
    main {{ width: min(1120px, calc(100vw - 32px)); margin: 0 auto; padding: 32px 0; }}
    h1, h2 {{ margin: 0; line-height: 1.15; }}
    h1 {{ font-size: 34px; }}
    .lead {{ margin: 10px 0 24px; color: #5e6875; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    article, section {{ border: 1px solid #d9ddd7; border-radius: 8px; background: #fff; box-shadow: 0 12px 30px rgba(24,33,43,.08); }}
    article {{ min-height: 86px; padding: 14px; }}
    article b {{ display: block; font-size: 13px; color: #5e6875; }}
    article span {{ display: block; margin-top: 8px; font-size: 18px; font-weight: 800; overflow-wrap: anywhere; }}
    .cols {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 16px; }}
    section {{ padding: 16px; }}
    ul {{ margin: 10px 0 0; padding-left: 18px; color: #5e6875; }}
    @media (max-width: 860px) {{ .grid, .cols {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>Channel Play Agent Company</h1>
    <p class=\"lead\">Shared memory, tasks, locks, reports, and worker state.</p>
    <div class=\"grid\">{stat_cards}</div>
    <div class=\"cols\">
      <section><h2>Tasks</h2><ul>{task_items}</ul></section>
      <section><h2>Locks</h2><ul>{lock_items}</ul></section>
    </div>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return paths.dashboard_html
