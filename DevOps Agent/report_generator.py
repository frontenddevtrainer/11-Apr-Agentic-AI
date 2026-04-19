"""
HTML Report Generator - Creates styled HTML reports summarizing errors and resolutions.
"""

import os
from datetime import datetime, timezone


def generate_html_report(analysis: dict) -> str:
    """Generate a styled HTML report from an analysis dictionary.

    Args:
        analysis: Dictionary with keys:
            - summary: Overall summary string
            - errors: List of dicts with 'service', 'level', 'message', 'resolution'
            - recommendations: List of recommendation strings
            - timestamp: ISO timestamp string

    Returns:
        Path to the generated HTML file.
    """
    timestamp = analysis.get("timestamp", datetime.now(timezone.utc).isoformat())
    summary = analysis.get("summary", "No summary available.")
    errors = analysis.get("errors", [])
    recommendations = analysis.get("recommendations", [])

    error_rows = ""
    for i, err in enumerate(errors, 1):
        level_class = "critical" if err.get("level") == "CRITICAL" else "error"
        error_rows += f"""
        <tr class="{level_class}">
            <td>{i}</td>
            <td><span class="badge badge-{level_class}">{err.get('level', 'ERROR')}</span></td>
            <td>{err.get('service', 'unknown')}</td>
            <td>{err.get('message', 'N/A')}</td>
            <td>{err.get('resolution', 'See runbook for details.')}</td>
        </tr>"""

    rec_items = ""
    for rec in recommendations:
        rec_items += f"<li>{rec}</li>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevOps Agent - Incident Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, #1e293b, #334155);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        h1 {{
            font-size: 1.8rem;
            color: #f1f5f9;
            margin-bottom: 0.5rem;
        }}
        h1 span {{ color: #60a5fa; }}
        .timestamp {{ color: #94a3b8; font-size: 0.9rem; }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .card h2 {{
            font-size: 1.2rem;
            color: #93c5fd;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #334155;
        }}
        .summary {{ line-height: 1.7; color: #cbd5e1; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
        }}
        th {{
            background: #334155;
            color: #93c5fd;
            padding: 0.75rem 1rem;
            text-align: left;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #334155;
            font-size: 0.9rem;
            vertical-align: top;
        }}
        tr:hover {{ background: #293548; }}
        tr.critical {{ border-left: 3px solid #ef4444; }}
        tr.error {{ border-left: 3px solid #f97316; }}
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-critical {{ background: #991b1b; color: #fca5a5; }}
        .badge-error {{ background: #9a3412; color: #fdba74; }}
        ul {{ list-style: none; padding: 0; }}
        ul li {{
            padding: 0.5rem 0 0.5rem 1.5rem;
            position: relative;
            color: #cbd5e1;
        }}
        ul li::before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #60a5fa;
            font-weight: bold;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .stat-card {{
            background: #334155;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 2rem;
            font-weight: 700;
            color: #f1f5f9;
        }}
        .stat-card .label {{ color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem; }}
        .stat-card.danger .number {{ color: #ef4444; }}
        .stat-card.warning .number {{ color: #f59e0b; }}
        .stat-card.success .number {{ color: #22c55e; }}
        footer {{
            text-align: center;
            color: #64748b;
            font-size: 0.8rem;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #334155;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔧 DevOps Agent <span>Incident Report</span></h1>
            <p class="timestamp">Generated: {timestamp}</p>
        </header>

        <div class="stats">
            <div class="stat-card danger">
                <div class="number">{sum(1 for e in errors if e.get('level') == 'CRITICAL')}</div>
                <div class="label">Critical</div>
            </div>
            <div class="stat-card warning">
                <div class="number">{sum(1 for e in errors if e.get('level') == 'ERROR')}</div>
                <div class="label">Errors</div>
            </div>
            <div class="stat-card success">
                <div class="number">{len(errors)}</div>
                <div class="label">Total Issues</div>
            </div>
        </div>

        <div class="card">
            <h2>Summary</h2>
            <p class="summary">{summary}</p>
        </div>

        <div class="card">
            <h2>Error Details & Resolutions</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Severity</th>
                        <th>Service</th>
                        <th>Error</th>
                        <th>Resolution</th>
                    </tr>
                </thead>
                <tbody>
                    {error_rows if error_rows else '<tr><td colspan="5" style="text-align:center;color:#64748b;">No errors found</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>Recommendations</h2>
            <ul>
                {rec_items if rec_items else '<li>No additional recommendations at this time.</li>'}
            </ul>
        </div>

        <footer>
            Generated by DevOps Agent • Powered by LangGraph + LangChain + OpenAI
        </footer>
    </div>
</body>
</html>"""

    report_path = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_path, exist_ok=True)
    filename = f"incident_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(report_path, filename)

    with open(filepath, "w") as f:
        f.write(html)

    print(f"Report generated: {filepath}")
    return filepath
