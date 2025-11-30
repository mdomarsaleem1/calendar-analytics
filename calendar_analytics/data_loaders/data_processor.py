"""Data processor for combining calendar and HRIS data."""

from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from ..models.calendar_event import CalendarEvent, Attendee
from ..models.employee import Employee, Organization


class DataProcessor:
    """
    Processes and enriches calendar data with HRIS information.

    Provides utilities for:
    - Combining calendar events with organizational data
    - Filtering and grouping events
    - Calculating aggregations
    """

    def __init__(self, organization: Organization):
        """
        Initialize the processor.

        Args:
            organization: Organization data from HRIS
        """
        self.org = organization

    def enrich_attendees(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """
        Enrich attendee information with HRIS data.

        Adds employee information to attendees where available.
        """
        for event in events:
            for attendee in event.attendees:
                employee = self.org.get_employee(attendee.email)
                if employee:
                    if not attendee.name:
                        attendee.name = employee.name
                    attendee.is_external = False
                else:
                    attendee.is_external = not self.org.is_internal_email(attendee.email)

        return events

    def filter_events_by_date_range(
        self,
        events: list[CalendarEvent],
        start_date: datetime,
        end_date: datetime
    ) -> list[CalendarEvent]:
        """Filter events within a date range."""
        return [
            e for e in events
            if start_date <= e.start_time <= end_date
        ]

    def filter_events_by_employee(
        self,
        events: list[CalendarEvent],
        email: str,
        as_organizer: bool = False,
        as_attendee: bool = True
    ) -> list[CalendarEvent]:
        """Filter events for a specific employee."""
        email_lower = email.lower()
        filtered = []

        for event in events:
            if as_organizer and event.is_organizer(email_lower):
                filtered.append(event)
            elif as_attendee and event.has_attendee(email_lower):
                filtered.append(event)

        return filtered

    def filter_non_cancelled(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Filter out cancelled events."""
        return [e for e in events if not e.is_cancelled]

    def filter_work_meetings(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Filter to only work meetings (exclude all-day events, focus time, etc.)."""
        return [
            e for e in events
            if not e.is_all_day
            and e.show_as != "free"
            and e.attendee_count > 1
        ]

    def group_events_by_week(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, list[CalendarEvent]]:
        """Group events by week (ISO week number)."""
        grouped: dict[str, list[CalendarEvent]] = defaultdict(list)

        for event in events:
            week_key = event.start_time.strftime("%Y-W%W")
            grouped[week_key].append(event)

        return dict(grouped)

    def group_events_by_month(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, list[CalendarEvent]]:
        """Group events by month."""
        grouped: dict[str, list[CalendarEvent]] = defaultdict(list)

        for event in events:
            month_key = event.start_time.strftime("%Y-%m")
            grouped[month_key].append(event)

        return dict(grouped)

    def group_events_by_day_of_week(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, list[CalendarEvent]]:
        """Group events by day of week."""
        grouped: dict[str, list[CalendarEvent]] = defaultdict(list)

        for event in events:
            grouped[event.day_of_week].append(event)

        return dict(grouped)

    def group_events_by_organizer(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, list[CalendarEvent]]:
        """Group events by organizer email."""
        grouped: dict[str, list[CalendarEvent]] = defaultdict(list)

        for event in events:
            grouped[event.organizer_email.lower()].append(event)

        return dict(grouped)

    def get_recurring_events(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Get only recurring events."""
        return [e for e in events if e.is_recurring]

    def get_adhoc_events(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Get only ad-hoc (non-recurring) events."""
        return [e for e in events if not e.is_recurring]

    def get_one_on_one_meetings(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Get only 1:1 meetings."""
        return [e for e in events if e.is_one_on_one]

    def get_external_meetings(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Get meetings with external attendees."""
        return [e for e in events if e.has_external_attendees]

    def get_internal_meetings(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Get meetings with only internal attendees."""
        return [e for e in events if not e.has_external_attendees]

    def calculate_total_meeting_hours(self, events: list[CalendarEvent]) -> float:
        """Calculate total meeting hours."""
        return sum(e.duration_hours for e in events)

    def calculate_average_meeting_duration(self, events: list[CalendarEvent]) -> float:
        """Calculate average meeting duration in minutes."""
        if not events:
            return 0
        return sum(e.duration_minutes for e in events) / len(events)

    def calculate_meeting_load_by_day(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, float]:
        """Calculate meeting hours per day of week."""
        by_day = self.group_events_by_day_of_week(events)
        return {
            day: self.calculate_total_meeting_hours(day_events)
            for day, day_events in by_day.items()
        }

    def find_back_to_back_meetings(
        self,
        events: list[CalendarEvent],
        buffer_minutes: int = 5
    ) -> list[tuple[CalendarEvent, CalendarEvent]]:
        """Find meetings that are back-to-back or have minimal gap."""
        if len(events) < 2:
            return []

        # Sort by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)
        back_to_back = []

        for i in range(len(sorted_events) - 1):
            current = sorted_events[i]
            next_event = sorted_events[i + 1]

            # Same day check
            if current.start_time.date() != next_event.start_time.date():
                continue

            gap = (next_event.start_time - current.end_time).total_seconds() / 60

            if gap <= buffer_minutes:
                back_to_back.append((current, next_event))

        return back_to_back

    def calculate_focus_time(
        self,
        events: list[CalendarEvent],
        work_start_hour: int = 9,
        work_end_hour: int = 18
    ) -> dict[str, float]:
        """
        Calculate available focus time (non-meeting time during work hours).

        Returns dict with date string keys and hours of focus time.
        """
        # Group by date
        by_date: dict[str, list[CalendarEvent]] = defaultdict(list)
        for event in events:
            date_key = event.start_time.strftime("%Y-%m-%d")
            by_date[date_key].append(event)

        focus_time = {}
        work_hours = work_end_hour - work_start_hour

        for date_str, day_events in by_date.items():
            meeting_hours = sum(e.duration_hours for e in day_events)
            focus_time[date_str] = max(0, work_hours - meeting_hours)

        return focus_time

    def get_meeting_participants_relationship(
        self,
        event: CalendarEvent
    ) -> dict:
        """
        Analyze relationships between meeting participants.

        Returns information about:
        - Same team members
        - Cross-functional participants
        - Manager-report relationships
        """
        participants = event.get_attendee_emails()
        employees = [self.org.get_employee(e) for e in participants]
        employees = [e for e in employees if e is not None]

        if len(employees) < 2:
            return {
                "same_team": False,
                "cross_functional": False,
                "has_manager_report": False,
                "functions_represented": [],
                "teams_represented": [],
            }

        # Check team membership
        teams = set(e.team for e in employees if e.team)
        functions = set(e.job_function for e in employees)

        # Check for manager-report relationships
        has_manager_report = False
        for emp in employees:
            for other in employees:
                if emp != other and emp.reports_to(other):
                    has_manager_report = True
                    break

        return {
            "same_team": len(teams) == 1 and len(teams) > 0,
            "cross_functional": len(functions) > 1,
            "has_manager_report": has_manager_report,
            "functions_represented": list(functions),
            "teams_represented": list(teams),
        }

    def identify_meeting_series(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, list[CalendarEvent]]:
        """
        Group events that appear to be the same recurring meeting series.

        Uses subject similarity and timing patterns.
        """
        series: dict[str, list[CalendarEvent]] = defaultdict(list)

        for event in events:
            if event.series_master_id:
                series[event.series_master_id].append(event)
            elif event.is_recurring:
                # Use subject as key for grouping
                key = event.subject.lower().strip()
                series[f"recurring:{key}"].append(event)
            else:
                series[f"adhoc:{event.event_id}"].append(event)

        return dict(series)

    def get_employee_meeting_stats(
        self,
        events: list[CalendarEvent],
        email: str
    ) -> dict:
        """Get comprehensive meeting statistics for an employee."""
        employee_events = self.filter_events_by_employee(events, email)
        employee = self.org.get_employee(email)

        organized = [e for e in employee_events if e.is_organizer(email)]
        attended = [e for e in employee_events if not e.is_organizer(email)]

        return {
            "email": email,
            "name": employee.name if employee else email,
            "total_meetings": len(employee_events),
            "meetings_organized": len(organized),
            "meetings_attended": len(attended),
            "total_hours": self.calculate_total_meeting_hours(employee_events),
            "hours_organized": self.calculate_total_meeting_hours(organized),
            "hours_attended": self.calculate_total_meeting_hours(attended),
            "avg_meeting_duration": self.calculate_average_meeting_duration(employee_events),
            "one_on_ones": len(self.get_one_on_one_meetings(employee_events)),
            "recurring_meetings": len(self.get_recurring_events(employee_events)),
            "external_meetings": len(self.get_external_meetings(employee_events)),
            "back_to_back_count": len(self.find_back_to_back_meetings(employee_events)),
        }
