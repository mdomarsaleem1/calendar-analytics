"""Main insights engine that orchestrates all analytics."""

from datetime import datetime
from typing import Optional

from ..models.calendar_event import CalendarEvent
from ..models.employee import Organization, JobFunction
from .meeting_analyzer import MeetingAnalyzer
from .manager_analytics import ManagerAnalytics
from .cross_functional import CrossFunctionalAnalyzer
from .text_analyzer import MeetingTextAnalyzer


class InsightsEngine:
    """
    Main engine that orchestrates all calendar analytics.

    Provides:
    - Comprehensive insights generation
    - Best practices recommendations
    - Internal vs external analysis
    - Performance optimization suggestions
    """

    def __init__(self, organization: Organization):
        """
        Initialize the insights engine.

        Args:
            organization: Organization data from HRIS
        """
        self.org = organization
        self.meeting_analyzer = MeetingAnalyzer(organization)
        self.manager_analytics = ManagerAnalytics(organization)
        self.cross_functional = CrossFunctionalAnalyzer(organization)
        self.text_analyzer = MeetingTextAnalyzer()

    def generate_full_insights(
        self,
        events: list[CalendarEvent],
        include_recommendations: bool = True
    ) -> dict:
        """
        Generate comprehensive insights from calendar data.

        Args:
            events: List of calendar events
            include_recommendations: Whether to include best practices recommendations

        Returns:
            Complete insights dictionary
        """
        # Filter to work meetings
        work_events = [
            e for e in events
            if not e.is_cancelled and not e.is_all_day and e.attendee_count > 1
        ]

        insights = {
            "summary": self._generate_summary(work_events),
            "size_duration_matrix": self.meeting_analyzer.analyze_size_duration_matrix(work_events).to_dict(),
            "recurring_vs_adhoc": self.meeting_analyzer.analyze_recurring_vs_adhoc(work_events, by_level=True),
            "one_on_one_vs_team": self.meeting_analyzer.analyze_one_on_one_vs_team(work_events),
            "timing_analysis": self.meeting_analyzer.analyze_meeting_timing(work_events),
            "efficiency_metrics": self.meeting_analyzer.analyze_meeting_efficiency(work_events),
            "calendar_fragmentation": self.meeting_analyzer.analyze_calendar_fragmentation(work_events),
            "internal_vs_external": self.analyze_internal_vs_external(work_events),
            "cross_functional_health": self.cross_functional.analyze_function_collaboration_health(work_events),
            "text_insights": self.text_analyzer.get_comprehensive_text_analysis(work_events),
        }

        # Manager-specific insights (only if we have managers)
        if self.org.get_all_managers():
            insights["manager_insights"] = {
                "span_of_control_impact": self.manager_analytics.analyze_span_of_control_impact(work_events),
                "at_risk_relationships": self.manager_analytics.identify_at_risk_relationships(work_events),
                "micromanagement_flags": self.manager_analytics.detect_micromanagement_patterns(work_events),
            }

        if include_recommendations:
            insights["best_practices"] = self.generate_best_practices_recommendations(work_events, insights)

        return insights

    def _generate_summary(self, events: list[CalendarEvent]) -> dict:
        """Generate executive summary of calendar analytics."""
        if not events:
            return {"error": "No events to analyze"}

        total_hours = sum(e.duration_hours for e in events)
        unique_days = len(set(e.start_time.date() for e in events))

        return {
            "total_meetings": len(events),
            "total_hours": round(total_hours, 2),
            "unique_days_analyzed": unique_days,
            "avg_meetings_per_day": round(len(events) / unique_days, 1) if unique_days else 0,
            "avg_hours_per_day": round(total_hours / unique_days, 1) if unique_days else 0,
            "avg_meeting_duration_minutes": round(
                sum(e.duration_minutes for e in events) / len(events), 1
            ),
            "avg_attendees": round(sum(e.attendee_count for e in events) / len(events), 1),
            "recurring_percentage": round(
                sum(1 for e in events if e.is_recurring) / len(events) * 100, 1
            ),
            "external_percentage": round(
                sum(1 for e in events if e.has_external_attendees) / len(events) * 100, 1
            ),
        }

    def analyze_internal_vs_external(
        self,
        events: list[CalendarEvent],
        by_function: bool = True
    ) -> dict:
        """
        Analyze internal vs external meeting patterns.

        Particularly relevant for Sales, Customer Success, and other
        customer-facing functions.
        """
        internal = [e for e in events if not e.has_external_attendees]
        external = [e for e in events if e.has_external_attendees]

        result = {
            "internal": {
                "count": len(internal),
                "hours": round(sum(e.duration_hours for e in internal), 2),
                "percentage": round(len(internal) / len(events) * 100, 1) if events else 0,
            },
            "external": {
                "count": len(external),
                "hours": round(sum(e.duration_hours for e in external), 2),
                "percentage": round(len(external) / len(events) * 100, 1) if events else 0,
                "avg_external_attendees": round(
                    sum(e.external_attendee_count for e in external) / len(external), 1
                ) if external else 0,
            },
        }

        # Analysis by function
        if by_function:
            function_external: dict[str, dict] = {}

            for func in JobFunction:
                func_employees = self.org.get_employees_by_function(func)
                func_emails = {e.email.lower() for e in func_employees}

                if not func_emails:
                    continue

                # Events organized by this function
                func_events = [
                    e for e in events
                    if e.organizer_email.lower() in func_emails
                ]

                if not func_events:
                    continue

                func_external_events = [e for e in func_events if e.has_external_attendees]

                function_external[func.value] = {
                    "total_meetings": len(func_events),
                    "external_meetings": len(func_external_events),
                    "external_percentage": round(
                        len(func_external_events) / len(func_events) * 100, 1
                    ),
                    "external_hours": round(
                        sum(e.duration_hours for e in func_external_events), 2
                    ),
                }

            result["by_function"] = function_external

            # Identify customer-facing functions (high external %)
            customer_facing = [
                {"function": func, **stats}
                for func, stats in function_external.items()
                if stats["external_percentage"] > 30
            ]
            result["customer_facing_functions"] = sorted(
                customer_facing,
                key=lambda x: x["external_percentage"],
                reverse=True
            )

        # External meeting patterns
        if external:
            # Time of day for external meetings
            external_by_hour: dict[int, int] = {}
            for e in external:
                hour = e.hour_of_day
                external_by_hour[hour] = external_by_hour.get(hour, 0) + 1

            peak_hour = max(external_by_hour.keys(), key=lambda h: external_by_hour[h])

            result["external_patterns"] = {
                "peak_hour": f"{peak_hour:02d}:00",
                "avg_duration_minutes": round(
                    sum(e.duration_minutes for e in external) / len(external), 1
                ),
                "recurring_percentage": round(
                    sum(1 for e in external if e.is_recurring) / len(external) * 100, 1
                ),
            }

        return result

    def analyze_individual(
        self,
        events: list[CalendarEvent],
        email: str
    ) -> dict:
        """
        Generate individual-level insights for a specific employee.
        """
        employee = self.org.get_employee(email)
        if not employee:
            return {"error": f"Employee not found: {email}"}

        # Filter events for this person
        person_events = [e for e in events if e.has_attendee(email)]
        organized = [e for e in person_events if e.is_organizer(email)]
        attended = [e for e in person_events if not e.is_organizer(email)]

        insights = {
            "employee": {
                "email": email,
                "name": employee.name,
                "title": employee.job_title,
                "function": employee.job_function.value,
                "level": employee.job_level.value,
                "is_manager": employee.is_people_manager,
                "direct_reports": employee.direct_report_count,
            },
            "summary": {
                "total_meetings": len(person_events),
                "meetings_organized": len(organized),
                "meetings_attended": len(attended),
                "total_hours": round(sum(e.duration_hours for e in person_events), 2),
                "avg_meeting_duration": round(
                    sum(e.duration_minutes for e in person_events) / len(person_events), 1
                ) if person_events else 0,
            },
            "size_duration": self.meeting_analyzer.analyze_size_duration_matrix(person_events).to_dict(),
            "meeting_types": self.meeting_analyzer.analyze_one_on_one_vs_team(person_events),
            "timing": self.meeting_analyzer.analyze_meeting_timing(person_events),
            "fragmentation": self.meeting_analyzer.analyze_calendar_fragmentation(person_events),
        }

        # Manager-specific analysis
        if employee.is_people_manager:
            insights["manager_allocation"] = self.manager_analytics.analyze_manager_time(
                events, email
            ).to_dict()

        return insights

    def generate_best_practices_recommendations(
        self,
        events: list[CalendarEvent],
        insights: dict
    ) -> dict:
        """
        Generate best practices recommendations based on meeting behavior.

        Returns actionable recommendations for improving meeting culture.
        """
        recommendations = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "positive_patterns": [],
        }

        summary = insights.get("summary", {})
        efficiency = insights.get("efficiency_metrics", {})
        fragmentation = insights.get("calendar_fragmentation", {})
        timing = insights.get("timing_analysis", {})
        text_insights = insights.get("text_insights", {})

        # HIGH PRIORITY RECOMMENDATIONS

        # Check meeting hours
        avg_hours = summary.get("avg_hours_per_day", 0)
        if avg_hours > 6:
            recommendations["high_priority"].append({
                "issue": "Excessive meeting time",
                "finding": f"Average {avg_hours:.1f} hours/day in meetings",
                "recommendation": "Reduce meeting time to 4-5 hours/day. Consider async alternatives for status updates.",
                "impact": "High - affects deep work and productivity",
            })
        elif avg_hours > 5:
            recommendations["medium_priority"].append({
                "issue": "High meeting load",
                "finding": f"Average {avg_hours:.1f} hours/day in meetings",
                "recommendation": "Review recurring meetings for necessity. Implement 'no meeting' time blocks.",
                "impact": "Medium - may limit focus time",
            })

        # Check average meeting duration
        avg_duration = summary.get("avg_meeting_duration_minutes", 0)
        if avg_duration > 50:
            recommendations["high_priority"].append({
                "issue": "Meetings default to 1 hour",
                "finding": f"Average meeting is {avg_duration:.0f} minutes",
                "recommendation": "Default to 25 or 50 minute meetings. Most discussions can be 25 mins.",
                "impact": "High - creates buffer time between meetings",
            })

        # Check fragmentation
        avg_fragmentation = fragmentation.get("avg_fragmentation_score", 0)
        if avg_fragmentation > 3:
            recommendations["high_priority"].append({
                "issue": "High calendar fragmentation",
                "finding": f"Fragmentation score: {avg_fragmentation:.1f}",
                "recommendation": "Cluster meetings together. Block focus time. Use meeting-free mornings.",
                "impact": "High - fragmented calendars reduce deep work by 40%+",
            })

        # MEDIUM PRIORITY RECOMMENDATIONS

        # Check response rates
        avg_response = efficiency.get("avg_response_rate", 100)
        if avg_response < 70:
            recommendations["medium_priority"].append({
                "issue": "Low meeting response rates",
                "finding": f"Only {avg_response:.0f}% of invitees respond",
                "recommendation": "Send calendar invites earlier. Include clear agendas. Follow up on non-responses.",
                "impact": "Medium - unclear attendance affects meeting effectiveness",
            })

        # Check recurring percentage
        recurring_pct = summary.get("recurring_percentage", 0)
        if recurring_pct > 70:
            recommendations["medium_priority"].append({
                "issue": "High recurring meeting percentage",
                "finding": f"{recurring_pct:.0f}% of meetings are recurring",
                "recommendation": "Review recurring meetings quarterly. Cancel or reduce frequency of low-value meetings.",
                "impact": "Medium - recurring meetings can become stale",
            })

        # Check large meetings
        large_over_10 = efficiency.get("large_meetings_over_10", 0)
        if large_over_10 > 5:
            recommendations["medium_priority"].append({
                "issue": "Many large meetings",
                "finding": f"{large_over_10} meetings with 10+ attendees",
                "recommendation": "Large meetings often have passive attendees. Consider smaller working groups.",
                "impact": "Medium - large meetings are often inefficient",
            })

        # Check meeting naming
        naming = text_insights.get("naming_patterns", {})
        vague_count = naming.get("vague_meeting_count", 0)
        total = summary.get("total_meetings", 1)
        if vague_count / total > 0.15:
            recommendations["medium_priority"].append({
                "issue": "Vague meeting names",
                "finding": f"{vague_count} meetings have generic names like 'Meeting' or 'Sync'",
                "recommendation": "Use descriptive names with action verbs (e.g., 'Review Q4 plan' not 'Meeting')",
                "impact": "Medium - clear names improve preparation and attendance",
            })

        # LOW PRIORITY RECOMMENDATIONS

        # Check early/late meetings
        early = timing.get("early_morning_meetings", {}).get("count", 0)
        late = timing.get("late_evening_meetings", {}).get("count", 0)
        unusual_hours = early + late

        if unusual_hours / total > 0.1:
            recommendations["low_priority"].append({
                "issue": "Meetings outside core hours",
                "finding": f"{unusual_hours} meetings before 9am or after 6pm",
                "recommendation": "Respect working hours when possible. Use async communication for non-urgent topics.",
                "impact": "Low - affects work-life balance",
            })

        # Check lunch meetings
        lunch = timing.get("lunch_time_meetings", {}).get("count", 0)
        if lunch / total > 0.1:
            recommendations["low_priority"].append({
                "issue": "Frequent lunch-time meetings",
                "finding": f"{lunch} meetings scheduled 12-1pm",
                "recommendation": "Keep lunch hour free when possible for breaks and informal connections.",
                "impact": "Low - affects wellbeing and informal networking",
            })

        # POSITIVE PATTERNS (things done well)

        # Good 1:1 ratio
        one_on_ones = insights.get("one_on_one_vs_team", {}).get("1:1", {})
        if one_on_ones.get("percentage_of_meetings", 0) >= 15:
            recommendations["positive_patterns"].append({
                "pattern": "Healthy 1:1 meeting ratio",
                "finding": f"{one_on_ones.get('percentage_of_meetings', 0):.0f}% of meetings are 1:1s",
                "benefit": "1:1s are effective for coaching, feedback, and relationship building",
            })

        # Good cross-functional collaboration
        cf_health = insights.get("cross_functional_health", {})
        if cf_health.get("health_score", 0) >= 60:
            recommendations["positive_patterns"].append({
                "pattern": "Good cross-functional collaboration",
                "finding": f"Collaboration health score: {cf_health.get('health_score', 0):.0f}/100",
                "benefit": "Strong cross-functional ties improve innovation and alignment",
            })

        # Standard meeting lengths
        standard_pct = efficiency.get("standard_length_percentage", 0)
        if standard_pct >= 80:
            recommendations["positive_patterns"].append({
                "pattern": "Consistent meeting lengths",
                "finding": f"{standard_pct:.0f}% of meetings use standard durations",
                "benefit": "Predictable meeting lengths help with calendar management",
            })

        return recommendations

    def generate_team_comparison(
        self,
        events: list[CalendarEvent],
        team_emails: dict[str, list[str]]
    ) -> dict:
        """
        Compare meeting patterns across teams.

        Args:
            events: All calendar events
            team_emails: Dict mapping team name to list of member emails

        Returns:
            Comparison metrics for each team
        """
        comparisons = {}

        for team_name, emails in team_emails.items():
            email_set = {e.lower() for e in emails}

            # Events involving team members
            team_events = [
                e for e in events
                if any(att.lower() in email_set for att in e.get_attendee_emails())
            ]

            if not team_events:
                continue

            comparisons[team_name] = {
                "member_count": len(emails),
                "total_meetings": len(team_events),
                "total_hours": round(sum(e.duration_hours for e in team_events), 2),
                "hours_per_person": round(
                    sum(e.duration_hours for e in team_events) / len(emails), 2
                ),
                "avg_meeting_duration": round(
                    sum(e.duration_minutes for e in team_events) / len(team_events), 1
                ),
                "recurring_pct": round(
                    sum(1 for e in team_events if e.is_recurring) / len(team_events) * 100, 1
                ),
                "external_pct": round(
                    sum(1 for e in team_events if e.has_external_attendees) / len(team_events) * 100, 1
                ),
                "one_on_one_pct": round(
                    sum(1 for e in team_events if e.is_one_on_one) / len(team_events) * 100, 1
                ),
            }

        # Add rankings
        if len(comparisons) > 1:
            metrics_to_rank = ["hours_per_person", "avg_meeting_duration", "recurring_pct"]

            for metric in metrics_to_rank:
                sorted_teams = sorted(
                    comparisons.keys(),
                    key=lambda t: comparisons[t][metric]
                )
                for rank, team in enumerate(sorted_teams, 1):
                    comparisons[team][f"{metric}_rank"] = rank

        return comparisons

    def export_insights(
        self,
        insights: dict,
        format: str = "json"
    ) -> str:
        """
        Export insights in various formats.

        Args:
            insights: Generated insights dictionary
            format: Output format (json, markdown, csv)

        Returns:
            Formatted string
        """
        import json

        if format == "json":
            return json.dumps(insights, indent=2, default=str)

        elif format == "markdown":
            return self._to_markdown(insights)

        else:
            return json.dumps(insights, indent=2, default=str)

    def _to_markdown(self, insights: dict) -> str:
        """Convert insights to markdown format."""
        md = []
        md.append("# Calendar Analytics Report\n")

        # Summary
        if "summary" in insights:
            md.append("## Executive Summary\n")
            summary = insights["summary"]
            md.append(f"- **Total Meetings**: {summary.get('total_meetings', 'N/A')}")
            md.append(f"- **Total Hours**: {summary.get('total_hours', 'N/A')}")
            md.append(f"- **Average per Day**: {summary.get('avg_meetings_per_day', 'N/A')} meetings, {summary.get('avg_hours_per_day', 'N/A')} hours")
            md.append(f"- **Average Duration**: {summary.get('avg_meeting_duration_minutes', 'N/A')} minutes")
            md.append("")

        # Best Practices
        if "best_practices" in insights:
            md.append("## Recommendations\n")

            bp = insights["best_practices"]

            if bp.get("high_priority"):
                md.append("### High Priority\n")
                for rec in bp["high_priority"]:
                    md.append(f"**{rec['issue']}**")
                    md.append(f"- Finding: {rec['finding']}")
                    md.append(f"- Recommendation: {rec['recommendation']}")
                    md.append("")

            if bp.get("medium_priority"):
                md.append("### Medium Priority\n")
                for rec in bp["medium_priority"]:
                    md.append(f"**{rec['issue']}**")
                    md.append(f"- Finding: {rec['finding']}")
                    md.append(f"- Recommendation: {rec['recommendation']}")
                    md.append("")

            if bp.get("positive_patterns"):
                md.append("### Positive Patterns\n")
                for pattern in bp["positive_patterns"]:
                    md.append(f"- {pattern['pattern']}: {pattern['finding']}")
                md.append("")

        return "\n".join(md)
