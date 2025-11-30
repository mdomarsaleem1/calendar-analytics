"""Report generation utilities for calendar analytics."""

import json
from datetime import datetime
from typing import Optional


class ReportGenerator:
    """
    Generates formatted reports from calendar analytics insights.

    Supports multiple output formats:
    - JSON
    - Markdown
    - HTML
    - CSV (for tabular data)
    """

    def __init__(self):
        """Initialize the report generator."""
        self.generated_at = datetime.now()

    def generate_executive_summary(self, insights: dict) -> str:
        """
        Generate a concise executive summary.

        Args:
            insights: Full insights dictionary

        Returns:
            Formatted executive summary
        """
        summary = insights.get("summary", {})
        best_practices = insights.get("best_practices", {})

        lines = [
            "=" * 60,
            "CALENDAR ANALYTICS - EXECUTIVE SUMMARY",
            "=" * 60,
            "",
            f"Analysis Period: {summary.get('unique_days_analyzed', 'N/A')} days",
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "KEY METRICS",
            "-" * 40,
            f"Total Meetings:          {summary.get('total_meetings', 'N/A'):>10}",
            f"Total Hours:             {summary.get('total_hours', 'N/A'):>10.1f}",
            f"Avg Meetings/Day:        {summary.get('avg_meetings_per_day', 'N/A'):>10.1f}",
            f"Avg Hours/Day:           {summary.get('avg_hours_per_day', 'N/A'):>10.1f}",
            f"Avg Meeting Duration:    {summary.get('avg_meeting_duration_minutes', 'N/A'):>10.0f} min",
            f"Avg Attendees:           {summary.get('avg_attendees', 'N/A'):>10.1f}",
            f"Recurring Meetings:      {summary.get('recurring_percentage', 'N/A'):>10.1f}%",
            f"External Meetings:       {summary.get('external_percentage', 'N/A'):>10.1f}%",
            "",
        ]

        # High priority issues
        high_priority = best_practices.get("high_priority", [])
        if high_priority:
            lines.extend([
                "HIGH PRIORITY ISSUES",
                "-" * 40,
            ])
            for issue in high_priority:
                lines.append(f"• {issue['issue']}")
                lines.append(f"  {issue['finding']}")
            lines.append("")

        # Positive patterns
        positive = best_practices.get("positive_patterns", [])
        if positive:
            lines.extend([
                "POSITIVE PATTERNS",
                "-" * 40,
            ])
            for pattern in positive:
                lines.append(f"• {pattern['pattern']}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_markdown_report(self, insights: dict, title: str = "Calendar Analytics Report") -> str:
        """
        Generate a comprehensive markdown report.

        Args:
            insights: Full insights dictionary
            title: Report title

        Returns:
            Markdown formatted report
        """
        md = []

        # Header
        md.append(f"# {title}")
        md.append(f"\n*Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M')}*\n")

        # Table of Contents
        md.append("## Table of Contents")
        md.append("1. [Executive Summary](#executive-summary)")
        md.append("2. [Meeting Size & Duration](#meeting-size--duration)")
        md.append("3. [Meeting Types](#meeting-types)")
        md.append("4. [Time Patterns](#time-patterns)")
        md.append("5. [Cross-Functional Collaboration](#cross-functional-collaboration)")
        md.append("6. [Recommendations](#recommendations)")
        md.append("")

        # Executive Summary
        md.append("## Executive Summary\n")
        summary = insights.get("summary", {})
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Total Meetings | {summary.get('total_meetings', 'N/A')} |")
        md.append(f"| Total Hours | {summary.get('total_hours', 'N/A'):.1f} |")
        md.append(f"| Days Analyzed | {summary.get('unique_days_analyzed', 'N/A')} |")
        md.append(f"| Avg Meetings/Day | {summary.get('avg_meetings_per_day', 'N/A'):.1f} |")
        md.append(f"| Avg Hours/Day | {summary.get('avg_hours_per_day', 'N/A'):.1f} |")
        md.append(f"| Avg Duration | {summary.get('avg_meeting_duration_minutes', 'N/A'):.0f} min |")
        md.append(f"| Recurring % | {summary.get('recurring_percentage', 'N/A'):.1f}% |")
        md.append(f"| External % | {summary.get('external_percentage', 'N/A'):.1f}% |")
        md.append("")

        # Size & Duration Matrix
        md.append("## Meeting Size & Duration\n")
        md.append("### 3x3 Matrix (Count / Hours)\n")

        matrix = insights.get("size_duration_matrix", {}).get("matrix", {})
        if matrix:
            md.append("| Size \\ Duration | Short (≤30m) | Medium (31-60m) | Long (>60m) |")
            md.append("|-----------------|--------------|-----------------|-------------|")

            for size in ["small", "medium", "large"]:
                size_data = matrix.get(size, {})
                short = size_data.get("short", {})
                medium = size_data.get("medium", {})
                long = size_data.get("long", {})

                md.append(
                    f"| {size.capitalize()} | "
                    f"{short.get('count', 0)} ({short.get('hours', 0):.1f}h) | "
                    f"{medium.get('count', 0)} ({medium.get('hours', 0):.1f}h) | "
                    f"{long.get('count', 0)} ({long.get('hours', 0):.1f}h) |"
                )
            md.append("")

        # Meeting Types
        md.append("## Meeting Types\n")
        md.append("### 1:1 vs Team Meetings\n")

        one_on_one = insights.get("one_on_one_vs_team", {})
        if one_on_one:
            md.append("| Type | Count | Hours | % of Meetings | % of Time |")
            md.append("|------|-------|-------|---------------|-----------|")

            for mtype, data in one_on_one.items():
                md.append(
                    f"| {mtype} | {data.get('count', 0)} | "
                    f"{data.get('hours', 0):.1f} | "
                    f"{data.get('percentage_of_meetings', 0):.1f}% | "
                    f"{data.get('percentage_of_time', 0):.1f}% |"
                )
            md.append("")

        # Recurring vs Ad-hoc
        md.append("### Recurring vs Ad-hoc\n")
        recurring = insights.get("recurring_vs_adhoc", {})
        if recurring:
            rec = recurring.get("recurring", {})
            adhoc = recurring.get("adhoc", {})

            md.append("| Type | Count | Hours | Avg Duration | Avg Attendees |")
            md.append("|------|-------|-------|--------------|---------------|")
            md.append(
                f"| Recurring | {rec.get('count', 0)} | "
                f"{rec.get('hours', 0):.1f} | "
                f"{rec.get('avg_duration_minutes', 0):.0f} min | "
                f"{rec.get('avg_attendees', 0):.1f} |"
            )
            md.append(
                f"| Ad-hoc | {adhoc.get('count', 0)} | "
                f"{adhoc.get('hours', 0):.1f} | "
                f"{adhoc.get('avg_duration_minutes', 0):.0f} min | "
                f"{adhoc.get('avg_attendees', 0):.1f} |"
            )
            md.append("")

        # Time Patterns
        md.append("## Time Patterns\n")
        timing = insights.get("timing_analysis", {})
        if timing:
            md.append(f"**Busiest Day:** {timing.get('busiest_day', 'N/A')}\n")
            md.append(f"**Peak Hour:** {timing.get('busiest_hour', 'N/A')}\n")

            early = timing.get("early_morning_meetings", {})
            late = timing.get("late_evening_meetings", {})
            lunch = timing.get("lunch_time_meetings", {})

            md.append("\n| Time Period | Meetings | Hours |")
            md.append("|-------------|----------|-------|")
            md.append(f"| Early Morning (<9am) | {early.get('count', 0)} | {early.get('hours', 0):.1f} |")
            md.append(f"| Lunch Time (12-1pm) | {lunch.get('count', 0)} | {lunch.get('hours', 0):.1f} |")
            md.append(f"| Late Evening (>6pm) | {late.get('count', 0)} | {late.get('hours', 0):.1f} |")
            md.append("")

        # Cross-Functional
        md.append("## Cross-Functional Collaboration\n")
        cf = insights.get("cross_functional_health", {})
        if cf:
            md.append(f"**Health Score:** {cf.get('health_score', 0):.0f}/100 ({cf.get('health_rating', 'N/A')})\n")
            md.append(f"**Cross-Functional Meetings:** {cf.get('cross_functional_percentage', 0):.1f}%\n")

            if cf.get("strongest_connections"):
                md.append("\n### Strongest Connections\n")
                for conn in cf["strongest_connections"][:3]:
                    md.append(f"- {conn.get('function_a', '')} ↔ {conn.get('function_b', '')}: {conn.get('meeting_count', 0)} meetings")
                md.append("")

        # Recommendations
        md.append("## Recommendations\n")
        bp = insights.get("best_practices", {})

        if bp.get("high_priority"):
            md.append("### 🔴 High Priority\n")
            for rec in bp["high_priority"]:
                md.append(f"**{rec['issue']}**")
                md.append(f"- *Finding:* {rec['finding']}")
                md.append(f"- *Recommendation:* {rec['recommendation']}")
                md.append(f"- *Impact:* {rec['impact']}")
                md.append("")

        if bp.get("medium_priority"):
            md.append("### 🟡 Medium Priority\n")
            for rec in bp["medium_priority"]:
                md.append(f"**{rec['issue']}**")
                md.append(f"- *Finding:* {rec['finding']}")
                md.append(f"- *Recommendation:* {rec['recommendation']}")
                md.append("")

        if bp.get("positive_patterns"):
            md.append("### 🟢 Positive Patterns\n")
            for pattern in bp["positive_patterns"]:
                md.append(f"- **{pattern['pattern']}**: {pattern['finding']}")
            md.append("")

        return "\n".join(md)

    def generate_html_report(self, insights: dict, title: str = "Calendar Analytics Report") -> str:
        """
        Generate an HTML report with basic styling.

        Args:
            insights: Full insights dictionary
            title: Report title

        Returns:
            HTML formatted report
        """
        md_content = self.generate_markdown_report(insights, title)

        # Simple HTML wrapper with styling
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; }}
        h3 {{ color: #27ae60; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .metric {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }}
    </style>
</head>
<body>
    <article>
        {self._md_to_html(md_content)}
    </article>
</body>
</html>"""

        return html

    def _md_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        import re

        html = markdown

        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

        # Tables (simple conversion)
        lines = html.split('\n')
        in_table = False
        result = []

        for line in lines:
            if '|' in line and not line.startswith('|--'):
                if not in_table:
                    result.append('<table>')
                    in_table = True

                cells = [c.strip() for c in line.split('|')[1:-1]]
                if result[-1] == '<table>':
                    result.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
                else:
                    result.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
            elif '|--' in line:
                continue  # Skip table separator
            else:
                if in_table:
                    result.append('</table>')
                    in_table = False
                result.append(line)

        if in_table:
            result.append('</table>')

        html = '\n'.join(result)

        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'

        return html

    def generate_json_report(self, insights: dict, pretty: bool = True) -> str:
        """
        Generate JSON formatted report.

        Args:
            insights: Full insights dictionary
            pretty: Whether to pretty-print the JSON

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(insights, indent=2, default=str)
        return json.dumps(insights, default=str)

    def save_report(
        self,
        insights: dict,
        output_path: str,
        format: str = "markdown"
    ) -> None:
        """
        Save report to file.

        Args:
            insights: Full insights dictionary
            output_path: Path to save the report
            format: Output format (markdown, html, json, text)
        """
        if format == "markdown":
            content = self.generate_markdown_report(insights)
        elif format == "html":
            content = self.generate_html_report(insights)
        elif format == "json":
            content = self.generate_json_report(insights)
        else:  # text
            content = self.generate_executive_summary(insights)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Report saved to: {output_path}")
