"""Core meeting analytics module."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from ..models.calendar_event import CalendarEvent, MeetingType
from ..models.employee import Organization, Employee, JobLevel


@dataclass
class SizeDurationMatrix:
    """3x3 matrix for meeting size vs duration analysis."""
    # Rows: small, medium, large (by attendee count)
    # Columns: short, medium, long (by duration)

    small_short: int = 0  # 1-2 people, ≤30 min
    small_medium: int = 0  # 1-2 people, 31-60 min
    small_long: int = 0  # 1-2 people, >60 min

    medium_short: int = 0  # 3-5 people, ≤30 min
    medium_medium: int = 0  # 3-5 people, 31-60 min
    medium_long: int = 0  # 3-5 people, >60 min

    large_short: int = 0  # 6+ people, ≤30 min
    large_medium: int = 0  # 6+ people, 31-60 min
    large_long: int = 0  # 6+ people, >60 min

    # Hours spent in each category
    small_short_hours: float = 0.0
    small_medium_hours: float = 0.0
    small_long_hours: float = 0.0
    medium_short_hours: float = 0.0
    medium_medium_hours: float = 0.0
    medium_long_hours: float = 0.0
    large_short_hours: float = 0.0
    large_medium_hours: float = 0.0
    large_long_hours: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "matrix": {
                "small": {
                    "short": {"count": self.small_short, "hours": round(self.small_short_hours, 2)},
                    "medium": {"count": self.small_medium, "hours": round(self.small_medium_hours, 2)},
                    "long": {"count": self.small_long, "hours": round(self.small_long_hours, 2)},
                },
                "medium": {
                    "short": {"count": self.medium_short, "hours": round(self.medium_short_hours, 2)},
                    "medium": {"count": self.medium_medium, "hours": round(self.medium_medium_hours, 2)},
                    "long": {"count": self.medium_long, "hours": round(self.medium_long_hours, 2)},
                },
                "large": {
                    "short": {"count": self.large_short, "hours": round(self.large_short_hours, 2)},
                    "medium": {"count": self.large_medium, "hours": round(self.large_medium_hours, 2)},
                    "long": {"count": self.large_long, "hours": round(self.large_long_hours, 2)},
                },
            },
            "total_meetings": self.total_meetings,
            "total_hours": round(self.total_hours, 2),
        }

    @property
    def total_meetings(self) -> int:
        return (
            self.small_short + self.small_medium + self.small_long +
            self.medium_short + self.medium_medium + self.medium_long +
            self.large_short + self.large_medium + self.large_long
        )

    @property
    def total_hours(self) -> float:
        return (
            self.small_short_hours + self.small_medium_hours + self.small_long_hours +
            self.medium_short_hours + self.medium_medium_hours + self.medium_long_hours +
            self.large_short_hours + self.large_medium_hours + self.large_long_hours
        )

    def get_time_distribution(self) -> dict[str, float]:
        """Get percentage of time in each category."""
        total = self.total_hours
        if total == 0:
            return {}

        return {
            "small_short_pct": round(self.small_short_hours / total * 100, 1),
            "small_medium_pct": round(self.small_medium_hours / total * 100, 1),
            "small_long_pct": round(self.small_long_hours / total * 100, 1),
            "medium_short_pct": round(self.medium_short_hours / total * 100, 1),
            "medium_medium_pct": round(self.medium_medium_hours / total * 100, 1),
            "medium_long_pct": round(self.medium_long_hours / total * 100, 1),
            "large_short_pct": round(self.large_short_hours / total * 100, 1),
            "large_medium_pct": round(self.large_medium_hours / total * 100, 1),
            "large_long_pct": round(self.large_long_hours / total * 100, 1),
        }


class MeetingAnalyzer:
    """
    Analyzes meeting patterns and generates insights.

    Provides analysis for:
    - Meeting size and duration patterns
    - Recurring vs ad-hoc meetings
    - 1:1 vs team meetings
    - Time utilization patterns
    """

    def __init__(self, organization: Optional[Organization] = None):
        """
        Initialize the analyzer.

        Args:
            organization: Optional organization data for enriched analysis
        """
        self.org = organization

    def analyze_size_duration_matrix(
        self,
        events: list[CalendarEvent]
    ) -> SizeDurationMatrix:
        """
        Create a 3x3 matrix of meeting size vs duration.

        Size categories:
        - Small: 1-2 attendees (including 1:1s)
        - Medium: 3-5 attendees
        - Large: 6+ attendees

        Duration categories:
        - Short: ≤30 minutes
        - Medium: 31-60 minutes
        - Long: >60 minutes
        """
        matrix = SizeDurationMatrix()

        for event in events:
            size = event.get_size_category()
            duration = event.get_duration_category()
            hours = event.duration_hours

            # Update counts and hours
            attr_count = f"{size}_{duration}"
            attr_hours = f"{size}_{duration}_hours"

            current_count = getattr(matrix, attr_count, 0)
            current_hours = getattr(matrix, attr_hours, 0.0)

            setattr(matrix, attr_count, current_count + 1)
            setattr(matrix, attr_hours, current_hours + hours)

        return matrix

    def analyze_recurring_vs_adhoc(
        self,
        events: list[CalendarEvent],
        by_level: bool = False
    ) -> dict:
        """
        Analyze split between recurring and ad-hoc meetings.

        Args:
            events: List of calendar events
            by_level: Whether to break down by job level

        Returns:
            Dictionary with recurring/ad-hoc statistics
        """
        recurring = [e for e in events if e.is_recurring]
        adhoc = [e for e in events if not e.is_recurring]

        result = {
            "recurring": {
                "count": len(recurring),
                "hours": round(sum(e.duration_hours for e in recurring), 2),
                "avg_duration_minutes": round(
                    sum(e.duration_minutes for e in recurring) / len(recurring), 1
                ) if recurring else 0,
                "avg_attendees": round(
                    sum(e.attendee_count for e in recurring) / len(recurring), 1
                ) if recurring else 0,
            },
            "adhoc": {
                "count": len(adhoc),
                "hours": round(sum(e.duration_hours for e in adhoc), 2),
                "avg_duration_minutes": round(
                    sum(e.duration_minutes for e in adhoc) / len(adhoc), 1
                ) if adhoc else 0,
                "avg_attendees": round(
                    sum(e.attendee_count for e in adhoc) / len(adhoc), 1
                ) if adhoc else 0,
            },
            "recurring_percentage": round(
                len(recurring) / len(events) * 100, 1
            ) if events else 0,
        }

        # Break down by level if organization data available
        if by_level and self.org:
            result["by_level"] = self._analyze_by_level(events, recurring, adhoc)

        return result

    def _analyze_by_level(
        self,
        all_events: list[CalendarEvent],
        recurring: list[CalendarEvent],
        adhoc: list[CalendarEvent]
    ) -> dict:
        """Analyze recurring/ad-hoc split by job level."""
        level_stats: dict[str, dict] = {}

        for level in JobLevel:
            employees = self.org.get_employees_by_level(level) if self.org else []
            emails = {e.email.lower() for e in employees}

            if not emails:
                continue

            level_recurring = [
                e for e in recurring
                if e.organizer_email.lower() in emails
            ]
            level_adhoc = [
                e for e in adhoc
                if e.organizer_email.lower() in emails
            ]

            total = len(level_recurring) + len(level_adhoc)
            if total == 0:
                continue

            level_stats[level.value] = {
                "recurring_count": len(level_recurring),
                "adhoc_count": len(level_adhoc),
                "recurring_percentage": round(len(level_recurring) / total * 100, 1),
                "total_meetings_organized": total,
            }

        return level_stats

    def analyze_one_on_one_vs_team(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Analyze distribution of 1:1 meetings vs team meetings.

        Returns breakdown of:
        - 1:1 meetings (2 participants)
        - Small team (3-5 participants)
        - Large team (6-10 participants)
        - All-hands (11+ participants)
        """
        distribution = {
            MeetingType.ONE_ON_ONE: [],
            MeetingType.SMALL_TEAM: [],
            MeetingType.LARGE_TEAM: [],
            MeetingType.ALL_HANDS: [],
            MeetingType.EXTERNAL: [],
        }

        for event in events:
            meeting_type = event.get_meeting_type()
            if meeting_type in distribution:
                distribution[meeting_type].append(event)

        result = {}
        total_events = len(events)
        total_hours = sum(e.duration_hours for e in events)

        for meeting_type, type_events in distribution.items():
            type_hours = sum(e.duration_hours for e in type_events)

            result[meeting_type.value] = {
                "count": len(type_events),
                "hours": round(type_hours, 2),
                "percentage_of_meetings": round(
                    len(type_events) / total_events * 100, 1
                ) if total_events else 0,
                "percentage_of_time": round(
                    type_hours / total_hours * 100, 1
                ) if total_hours else 0,
                "avg_duration_minutes": round(
                    sum(e.duration_minutes for e in type_events) / len(type_events), 1
                ) if type_events else 0,
            }

        return result

    def analyze_meeting_timing(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Analyze meeting timing patterns.

        Returns:
        - Distribution by day of week
        - Distribution by hour of day
        - Early/late meeting patterns
        """
        by_day: dict[str, list] = defaultdict(list)
        by_hour: dict[int, list] = defaultdict(list)

        for event in events:
            by_day[event.day_of_week].append(event)
            by_hour[event.hour_of_day].append(event)

        # Day of week analysis
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_stats = {}

        for day in day_order:
            day_events = by_day.get(day, [])
            day_stats[day] = {
                "count": len(day_events),
                "hours": round(sum(e.duration_hours for e in day_events), 2),
            }

        # Hour of day analysis
        hour_stats = {}
        for hour in range(24):
            hour_events = by_hour.get(hour, [])
            hour_stats[f"{hour:02d}:00"] = {
                "count": len(hour_events),
                "hours": round(sum(e.duration_hours for e in hour_events), 2),
            }

        # Special timing patterns
        early_meetings = [e for e in events if e.is_early_morning]
        late_meetings = [e for e in events if e.is_late_evening]
        lunch_meetings = [e for e in events if e.is_lunch_time]

        return {
            "by_day_of_week": day_stats,
            "by_hour": hour_stats,
            "early_morning_meetings": {
                "count": len(early_meetings),
                "hours": round(sum(e.duration_hours for e in early_meetings), 2),
            },
            "late_evening_meetings": {
                "count": len(late_meetings),
                "hours": round(sum(e.duration_hours for e in late_meetings), 2),
            },
            "lunch_time_meetings": {
                "count": len(lunch_meetings),
                "hours": round(sum(e.duration_hours for e in lunch_meetings), 2),
            },
            "busiest_day": max(day_stats.keys(), key=lambda d: day_stats[d]["hours"]) if day_stats else None,
            "busiest_hour": max(hour_stats.keys(), key=lambda h: hour_stats[h]["count"]) if hour_stats else None,
        }

    def analyze_meeting_efficiency(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Analyze meeting efficiency metrics.

        Metrics include:
        - Response rates
        - Acceptance rates
        - Meeting length patterns
        - Attendee count patterns
        """
        if not events:
            return {}

        response_rates = [e.get_response_rate() for e in events]
        acceptance_rates = [e.get_acceptance_rate() for e in events]
        durations = [e.duration_minutes for e in events]
        attendee_counts = [e.attendee_count for e in events]

        # Analyze standard meeting lengths
        standard_lengths = {30: 0, 60: 0, 15: 0, 45: 0, 90: 0}
        for duration in durations:
            if duration in standard_lengths:
                standard_lengths[duration] += 1

        # Meetings ending on time vs running over
        round_number_meetings = sum(
            1 for d in durations
            if d in [15, 30, 45, 60, 90, 120]
        )

        return {
            "avg_response_rate": round(sum(response_rates) / len(response_rates) * 100, 1),
            "avg_acceptance_rate": round(sum(acceptance_rates) / len(acceptance_rates) * 100, 1),
            "avg_duration_minutes": round(sum(durations) / len(durations), 1),
            "median_duration_minutes": sorted(durations)[len(durations) // 2],
            "avg_attendees": round(sum(attendee_counts) / len(attendee_counts), 1),
            "median_attendees": sorted(attendee_counts)[len(attendee_counts) // 2],
            "standard_length_meetings": {
                "15_min": standard_lengths[15],
                "30_min": standard_lengths[30],
                "45_min": standard_lengths[45],
                "60_min": standard_lengths[60],
                "90_min": standard_lengths[90],
            },
            "standard_length_percentage": round(
                round_number_meetings / len(events) * 100, 1
            ),
            "meetings_over_1_hour": sum(1 for d in durations if d > 60),
            "meetings_over_2_hours": sum(1 for d in durations if d > 120),
            "large_meetings_over_10": sum(1 for c in attendee_counts if c > 10),
        }

    def analyze_calendar_fragmentation(
        self,
        events: list[CalendarEvent],
        work_start: int = 9,
        work_end: int = 18
    ) -> dict:
        """
        Analyze calendar fragmentation and focus time.

        Fragmentation indicates how scattered meetings are throughout the day,
        which can impact deep work and productivity.
        """
        from collections import defaultdict

        # Group events by date
        by_date: dict[str, list] = defaultdict(list)
        for event in events:
            date_key = event.start_time.strftime("%Y-%m-%d")
            by_date[date_key].append(event)

        daily_stats = []

        for date_str, day_events in by_date.items():
            # Sort by start time
            sorted_events = sorted(day_events, key=lambda e: e.start_time)

            if not sorted_events:
                continue

            # Calculate gaps between meetings
            gaps = []
            for i in range(len(sorted_events) - 1):
                current_end = sorted_events[i].end_time
                next_start = sorted_events[i + 1].start_time
                gap_minutes = (next_start - current_end).total_seconds() / 60
                if gap_minutes > 0:
                    gaps.append(gap_minutes)

            # Calculate metrics
            total_meeting_hours = sum(e.duration_hours for e in sorted_events)
            work_hours = work_end - work_start

            # Focus blocks: gaps of 60+ minutes
            focus_blocks = [g for g in gaps if g >= 60]

            # Fragmentation score (higher = more fragmented)
            # Based on number of transitions and average gap size
            fragmentation = len(sorted_events) / max(total_meeting_hours, 1)

            daily_stats.append({
                "date": date_str,
                "meeting_count": len(sorted_events),
                "meeting_hours": round(total_meeting_hours, 2),
                "available_focus_time_hours": round(work_hours - total_meeting_hours, 2),
                "focus_blocks_60min_plus": len(focus_blocks),
                "avg_gap_minutes": round(sum(gaps) / len(gaps), 1) if gaps else 0,
                "fragmentation_score": round(fragmentation, 2),
            })

        if not daily_stats:
            return {}

        return {
            "daily_stats": daily_stats,
            "avg_meetings_per_day": round(
                sum(d["meeting_count"] for d in daily_stats) / len(daily_stats), 1
            ),
            "avg_meeting_hours_per_day": round(
                sum(d["meeting_hours"] for d in daily_stats) / len(daily_stats), 1
            ),
            "avg_focus_hours_per_day": round(
                sum(d["available_focus_time_hours"] for d in daily_stats) / len(daily_stats), 1
            ),
            "avg_fragmentation_score": round(
                sum(d["fragmentation_score"] for d in daily_stats) / len(daily_stats), 2
            ),
            "days_with_no_focus_blocks": sum(
                1 for d in daily_stats if d["focus_blocks_60min_plus"] == 0
            ),
        }

    def analyze_meeting_cost(
        self,
        events: list[CalendarEvent],
        avg_hourly_rate: float = 75.0
    ) -> dict:
        """
        Estimate meeting costs based on attendee hours.

        Args:
            events: List of calendar events
            avg_hourly_rate: Average hourly cost per employee

        Returns:
            Cost analysis including total cost, cost per meeting, etc.
        """
        total_attendee_hours = sum(
            e.duration_hours * e.attendee_count
            for e in events
        )

        total_cost = total_attendee_hours * avg_hourly_rate

        # By meeting type
        type_costs = {}
        for meeting_type in MeetingType:
            type_events = [e for e in events if e.get_meeting_type() == meeting_type]
            type_hours = sum(e.duration_hours * e.attendee_count for e in type_events)
            type_costs[meeting_type.value] = {
                "hours": round(type_hours, 2),
                "estimated_cost": round(type_hours * avg_hourly_rate, 2),
            }

        return {
            "total_attendee_hours": round(total_attendee_hours, 2),
            "total_estimated_cost": round(total_cost, 2),
            "avg_cost_per_meeting": round(total_cost / len(events), 2) if events else 0,
            "by_meeting_type": type_costs,
            "hourly_rate_used": avg_hourly_rate,
        }
