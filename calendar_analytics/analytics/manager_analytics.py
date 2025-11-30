"""Manager-specific analytics for leadership time analysis."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from ..models.calendar_event import CalendarEvent, MeetingCategory
from ..models.employee import Organization, Employee, JobLevel


@dataclass
class ManagerTimeAllocation:
    """Time allocation breakdown for a manager."""
    manager_email: str
    manager_name: str
    direct_report_count: int
    total_meeting_hours: float = 0.0

    # Time in different activities
    one_on_one_hours: float = 0.0
    skip_level_hours: float = 0.0
    team_meeting_hours: float = 0.0
    cross_functional_hours: float = 0.0
    external_hours: float = 0.0
    status_update_hours: float = 0.0
    strategic_hours: float = 0.0
    operational_hours: float = 0.0

    # Counts
    one_on_one_count: int = 0
    skip_level_count: int = 0
    team_meeting_count: int = 0
    meetings_with_reports: int = 0

    def to_dict(self) -> dict:
        return {
            "manager_email": self.manager_email,
            "manager_name": self.manager_name,
            "direct_report_count": self.direct_report_count,
            "total_meeting_hours": round(self.total_meeting_hours, 2),
            "time_allocation": {
                "one_on_one_hours": round(self.one_on_one_hours, 2),
                "skip_level_hours": round(self.skip_level_hours, 2),
                "team_meeting_hours": round(self.team_meeting_hours, 2),
                "cross_functional_hours": round(self.cross_functional_hours, 2),
                "external_hours": round(self.external_hours, 2),
                "status_update_hours": round(self.status_update_hours, 2),
                "strategic_hours": round(self.strategic_hours, 2),
                "operational_hours": round(self.operational_hours, 2),
            },
            "meeting_counts": {
                "one_on_ones": self.one_on_one_count,
                "skip_levels": self.skip_level_count,
                "team_meetings": self.team_meeting_count,
                "with_direct_reports": self.meetings_with_reports,
            },
            "percentages": self.get_percentages(),
            "insights": self.generate_insights(),
        }

    def get_percentages(self) -> dict:
        """Calculate percentage breakdown of time."""
        if self.total_meeting_hours == 0:
            return {}

        return {
            "one_on_one_pct": round(self.one_on_one_hours / self.total_meeting_hours * 100, 1),
            "skip_level_pct": round(self.skip_level_hours / self.total_meeting_hours * 100, 1),
            "team_meeting_pct": round(self.team_meeting_hours / self.total_meeting_hours * 100, 1),
            "cross_functional_pct": round(self.cross_functional_hours / self.total_meeting_hours * 100, 1),
            "external_pct": round(self.external_hours / self.total_meeting_hours * 100, 1),
        }

    @property
    def one_on_one_ratio(self) -> float:
        """Ratio of 1:1 time to total meeting time."""
        if self.total_meeting_hours == 0:
            return 0
        return self.one_on_one_hours / self.total_meeting_hours

    @property
    def coaching_time_per_report(self) -> float:
        """Average 1:1 hours per direct report."""
        if self.direct_report_count == 0:
            return 0
        return self.one_on_one_hours / self.direct_report_count

    @property
    def monitoring_indicator(self) -> float:
        """
        Indicator of potential over-monitoring.

        Higher values suggest more monitoring behavior:
        - High status update meeting attendance
        - Many meetings with reports beyond 1:1s
        - Low ratio of 1:1 to total report interaction
        """
        if self.meetings_with_reports == 0:
            return 0

        # Factor 1: Status meetings as portion of report interactions
        status_ratio = self.status_update_hours / max(self.total_meeting_hours, 1)

        # Factor 2: Group meetings with reports vs 1:1s
        group_meetings_with_reports = self.meetings_with_reports - self.one_on_one_count
        group_ratio = group_meetings_with_reports / max(self.one_on_one_count, 1)

        # Combined score (0-10 scale)
        score = (status_ratio * 5) + min(group_ratio * 2, 5)
        return round(min(score, 10), 1)

    def generate_insights(self) -> list[str]:
        """Generate actionable insights for this manager."""
        insights = []

        pcts = self.get_percentages()
        one_on_one_pct = pcts.get("one_on_one_pct", 0)

        # 1:1 time analysis
        if one_on_one_pct < 15 and self.direct_report_count > 0:
            insights.append(
                f"Low 1:1 time ({one_on_one_pct}%). Consider increasing direct "
                f"coaching time with {self.direct_report_count} reports."
            )
        elif one_on_one_pct > 40:
            insights.append(
                f"High 1:1 time ({one_on_one_pct}%). Ensure team alignment "
                "through group discussions isn't being missed."
            )

        # Coaching time per report
        if self.direct_report_count > 0:
            hours_per_report = self.coaching_time_per_report
            # Assuming monthly data, ~2-4 hours/month is healthy
            if hours_per_report < 1:
                insights.append(
                    f"Only {hours_per_report:.1f} hrs/report in 1:1s. "
                    "Consider more frequent check-ins."
                )

        # Monitoring indicator
        if self.monitoring_indicator > 6:
            insights.append(
                f"High monitoring score ({self.monitoring_indicator}/10). "
                "Consider empowering team with more autonomy."
            )

        # Skip-level engagement
        if self.skip_level_count == 0 and self.direct_report_count > 3:
            insights.append(
                "No skip-level meetings detected. Consider connecting "
                "with reports' teams for broader visibility."
            )

        # Strategic vs operational balance
        strategic_pct = pcts.get("strategic_pct", 0) if "strategic_pct" in pcts else (
            self.strategic_hours / max(self.total_meeting_hours, 1) * 100
        )
        if strategic_pct < 10 and self.total_meeting_hours > 20:
            insights.append(
                "Low strategic meeting time. Ensure sufficient focus on "
                "long-term planning and vision work."
            )

        return insights


class ManagerAnalytics:
    """
    Analytics specifically for managers and leadership.

    Analyzes:
    - Time spent in 1:1s vs group meetings
    - Monitoring/micromanagement patterns
    - Skip-level engagement
    - Team coverage
    - Leadership effectiveness indicators
    """

    def __init__(self, organization: Organization):
        """
        Initialize with organization data.

        Args:
            organization: Organization with employee/manager relationships
        """
        self.org = organization

    def analyze_manager_time(
        self,
        events: list[CalendarEvent],
        manager_email: str
    ) -> ManagerTimeAllocation:
        """
        Analyze time allocation for a specific manager.

        Args:
            events: All calendar events (will be filtered for this manager)
            manager_email: Email of the manager to analyze

        Returns:
            ManagerTimeAllocation with detailed breakdown
        """
        manager = self.org.get_employee(manager_email)
        if not manager:
            return ManagerTimeAllocation(
                manager_email=manager_email,
                manager_name=manager_email,
                direct_report_count=0,
            )

        # Get direct reports
        direct_reports = self.org.get_direct_reports(manager_email)
        report_emails = {r.email.lower() for r in direct_reports}

        # Get skip-level reports (reports of direct reports)
        skip_level_emails: set[str] = set()
        for report in direct_reports:
            skip_reports = self.org.get_direct_reports(report.email)
            skip_level_emails.update(r.email.lower() for r in skip_reports)

        # Filter events for this manager
        manager_events = [
            e for e in events
            if e.has_attendee(manager_email)
        ]

        allocation = ManagerTimeAllocation(
            manager_email=manager_email,
            manager_name=manager.name,
            direct_report_count=len(direct_reports),
            total_meeting_hours=sum(e.duration_hours for e in manager_events),
        )

        for event in manager_events:
            hours = event.duration_hours
            attendees = {a.email.lower() for a in event.attendees}
            attendees.add(event.organizer_email.lower())
            attendees.discard(manager_email.lower())

            # Check meeting type
            category = event.classify_meeting_category()

            # 1:1 with direct report
            if event.is_one_on_one and attendees & report_emails:
                allocation.one_on_one_hours += hours
                allocation.one_on_one_count += 1
                allocation.meetings_with_reports += 1

            # Skip-level meetings
            elif event.is_one_on_one and attendees & skip_level_emails:
                allocation.skip_level_hours += hours
                allocation.skip_level_count += 1

            # Team meetings (multiple direct reports present)
            elif len(attendees & report_emails) > 1:
                allocation.team_meeting_hours += hours
                allocation.team_meeting_count += 1
                allocation.meetings_with_reports += 1

            # Any meeting with at least one direct report
            elif attendees & report_emails:
                allocation.meetings_with_reports += 1

            # External meetings
            if event.has_external_attendees:
                allocation.external_hours += hours

            # Cross-functional (attendees from different departments)
            else:
                functions = set()
                for email in attendees:
                    emp = self.org.get_employee(email)
                    if emp:
                        functions.add(emp.job_function)
                if len(functions) > 1:
                    allocation.cross_functional_hours += hours

            # Category-based time
            if category == MeetingCategory.STATUS_UPDATE:
                allocation.status_update_hours += hours
            elif category == MeetingCategory.STRATEGIC:
                allocation.strategic_hours += hours
            elif category == MeetingCategory.OPERATIONAL:
                allocation.operational_hours += hours

        return allocation

    def analyze_all_managers(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, ManagerTimeAllocation]:
        """
        Analyze time allocation for all managers in the organization.

        Returns:
            Dictionary mapping manager email to their time allocation
        """
        managers = self.org.get_all_managers()
        results = {}

        for manager in managers:
            allocation = self.analyze_manager_time(events, manager.email)
            results[manager.email] = allocation

        return results

    def get_manager_leaderboard(
        self,
        events: list[CalendarEvent],
        metric: str = "one_on_one_ratio"
    ) -> list[dict]:
        """
        Rank managers by a specific metric.

        Available metrics:
        - one_on_one_ratio: Ratio of 1:1 time to total meeting time
        - coaching_time_per_report: Average 1:1 hours per direct report
        - monitoring_indicator: Lower is better (inverse ranking)
        - skip_level_engagement: Skip-level meeting count

        Returns:
            Sorted list of manager stats
        """
        allocations = self.analyze_all_managers(events)

        leaderboard = []
        for email, allocation in allocations.items():
            if allocation.direct_report_count == 0:
                continue

            score = 0
            if metric == "one_on_one_ratio":
                score = allocation.one_on_one_ratio
            elif metric == "coaching_time_per_report":
                score = allocation.coaching_time_per_report
            elif metric == "monitoring_indicator":
                score = -allocation.monitoring_indicator  # Invert for ranking
            elif metric == "skip_level_engagement":
                score = allocation.skip_level_count

            leaderboard.append({
                "email": email,
                "name": allocation.manager_name,
                "direct_reports": allocation.direct_report_count,
                "score": round(score, 2),
                "metric": metric,
                "details": allocation.to_dict(),
            })

        # Sort by score descending
        leaderboard.sort(key=lambda x: x["score"], reverse=True)

        return leaderboard

    def identify_at_risk_relationships(
        self,
        events: list[CalendarEvent],
        min_one_on_one_hours_monthly: float = 1.0
    ) -> list[dict]:
        """
        Identify manager-report relationships that may need attention.

        Flags relationships where:
        - No 1:1s in the analysis period
        - Very low 1:1 time
        - High ratio of group to 1:1 interactions
        """
        at_risk = []
        managers = self.org.get_all_managers()

        for manager in managers:
            direct_reports = self.org.get_direct_reports(manager.email)

            for report in direct_reports:
                # Find 1:1 meetings between this pair
                one_on_ones = [
                    e for e in events
                    if e.is_one_on_one
                    and e.has_attendee(manager.email)
                    and e.has_attendee(report.email)
                ]

                one_on_one_hours = sum(e.duration_hours for e in one_on_ones)

                # Find all meetings together
                all_meetings = [
                    e for e in events
                    if e.has_attendee(manager.email)
                    and e.has_attendee(report.email)
                ]

                total_hours = sum(e.duration_hours for e in all_meetings)

                # Check for at-risk indicators
                risk_factors = []

                if len(one_on_ones) == 0:
                    risk_factors.append("No 1:1 meetings")

                if one_on_one_hours < min_one_on_one_hours_monthly:
                    risk_factors.append(f"Low 1:1 time ({one_on_one_hours:.1f} hrs)")

                if total_hours > 0 and one_on_one_hours / total_hours < 0.3:
                    ratio = one_on_one_hours / total_hours * 100
                    risk_factors.append(f"1:1 only {ratio:.0f}% of interaction time")

                if risk_factors:
                    at_risk.append({
                        "manager_email": manager.email,
                        "manager_name": manager.name,
                        "report_email": report.email,
                        "report_name": report.name,
                        "one_on_one_count": len(one_on_ones),
                        "one_on_one_hours": round(one_on_one_hours, 2),
                        "total_meeting_hours": round(total_hours, 2),
                        "risk_factors": risk_factors,
                    })

        return at_risk

    def analyze_span_of_control_impact(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Analyze how span of control (number of direct reports) impacts
        manager time allocation.
        """
        allocations = self.analyze_all_managers(events)

        # Group by span of control
        by_span: dict[str, list] = defaultdict(list)

        for allocation in allocations.values():
            if allocation.direct_report_count == 0:
                continue

            span = allocation.direct_report_count
            if span <= 3:
                span_category = "small (1-3)"
            elif span <= 6:
                span_category = "medium (4-6)"
            elif span <= 10:
                span_category = "large (7-10)"
            else:
                span_category = "very_large (11+)"

            by_span[span_category].append(allocation)

        results = {}
        for span_category, allocations_list in by_span.items():
            if not allocations_list:
                continue

            results[span_category] = {
                "manager_count": len(allocations_list),
                "avg_one_on_one_ratio": round(
                    sum(a.one_on_one_ratio for a in allocations_list) / len(allocations_list), 2
                ),
                "avg_coaching_per_report": round(
                    sum(a.coaching_time_per_report for a in allocations_list) / len(allocations_list), 2
                ),
                "avg_monitoring_score": round(
                    sum(a.monitoring_indicator for a in allocations_list) / len(allocations_list), 1
                ),
                "avg_total_meeting_hours": round(
                    sum(a.total_meeting_hours for a in allocations_list) / len(allocations_list), 1
                ),
            }

        return results

    def detect_micromanagement_patterns(
        self,
        events: list[CalendarEvent],
        threshold_score: float = 6.0
    ) -> list[dict]:
        """
        Identify managers who may be exhibiting micromanagement patterns.

        Indicators:
        - High monitoring indicator score
        - Many status meetings with same people
        - Low autonomy signals (high meeting frequency with reports)
        """
        allocations = self.analyze_all_managers(events)
        flagged = []

        for email, allocation in allocations.items():
            if allocation.direct_report_count == 0:
                continue

            if allocation.monitoring_indicator >= threshold_score:
                manager = self.org.get_employee(email)

                # Additional analysis
                report_meeting_frequency = (
                    allocation.meetings_with_reports / max(allocation.direct_report_count, 1)
                )

                flagged.append({
                    "manager_email": email,
                    "manager_name": manager.name if manager else email,
                    "direct_reports": allocation.direct_report_count,
                    "monitoring_score": allocation.monitoring_indicator,
                    "status_meeting_hours": round(allocation.status_update_hours, 2),
                    "meetings_per_report": round(report_meeting_frequency, 1),
                    "one_on_one_ratio": round(allocation.one_on_one_ratio * 100, 1),
                    "recommendations": [
                        "Consider reducing status update meetings",
                        "Delegate more decision-making to team",
                        "Focus 1:1s on coaching rather than status",
                        "Establish async communication channels for updates",
                    ],
                })

        # Sort by monitoring score
        flagged.sort(key=lambda x: x["monitoring_score"], reverse=True)

        return flagged
