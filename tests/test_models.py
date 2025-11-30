"""Tests for data models."""

import pytest
from datetime import datetime, timedelta

from calendar_analytics.models.calendar_event import (
    CalendarEvent,
    Attendee,
    AttendeeResponse,
    MeetingType,
    MeetingCategory,
)
from calendar_analytics.models.employee import (
    Employee,
    Organization,
    JobLevel,
    JobFunction,
)


class TestCalendarEvent:
    """Tests for CalendarEvent model."""

    def test_duration_calculation(self):
        """Test meeting duration calculations."""
        event = CalendarEvent(
            event_id="test1",
            subject="Test Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )

        assert event.duration_minutes == 60
        assert event.duration_hours == 1.0

    def test_attendee_count(self):
        """Test attendee counting."""
        event = CalendarEvent(
            event_id="test1",
            subject="Test Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
            attendees=[
                Attendee(email="attendee1@example.com"),
                Attendee(email="attendee2@example.com"),
            ],
        )

        assert event.attendee_count == 3  # 2 attendees + organizer

    def test_is_one_on_one(self):
        """Test 1:1 meeting detection."""
        event = CalendarEvent(
            event_id="test1",
            subject="1:1 Meeting",
            organizer_email="manager@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 10, 30),
            attendees=[
                Attendee(email="report@example.com"),
            ],
        )

        assert event.is_one_on_one is True
        assert event.get_meeting_type() == MeetingType.ONE_ON_ONE

    def test_external_attendee_detection(self):
        """Test external attendee detection."""
        event = CalendarEvent(
            event_id="test1",
            subject="Client Meeting",
            organizer_email="sales@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
            attendees=[
                Attendee(email="client@external.com", is_external=True),
                Attendee(email="colleague@example.com", is_external=False),
            ],
        )

        assert event.has_external_attendees is True
        assert event.external_attendee_count == 1
        assert event.internal_attendee_count == 2  # colleague + organizer

    def test_size_category(self):
        """Test meeting size categorization."""
        # Small meeting (1-2 people)
        small_event = CalendarEvent(
            event_id="small",
            subject="Small Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 10, 30),
            attendees=[Attendee(email="attendee@example.com")],
        )
        assert small_event.get_size_category() == "small"

        # Medium meeting (3-5 people)
        medium_event = CalendarEvent(
            event_id="medium",
            subject="Medium Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 10, 30),
            attendees=[
                Attendee(email=f"attendee{i}@example.com")
                for i in range(3)
            ],
        )
        assert medium_event.get_size_category() == "medium"

        # Large meeting (6+ people)
        large_event = CalendarEvent(
            event_id="large",
            subject="Large Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 10, 30),
            attendees=[
                Attendee(email=f"attendee{i}@example.com")
                for i in range(10)
            ],
        )
        assert large_event.get_size_category() == "large"

    def test_duration_category(self):
        """Test meeting duration categorization."""
        # Short (≤30 min)
        short_event = CalendarEvent(
            event_id="short",
            subject="Short Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 10, 30),
        )
        assert short_event.get_duration_category() == "short"

        # Medium (31-60 min)
        medium_event = CalendarEvent(
            event_id="medium",
            subject="Medium Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )
        assert medium_event.get_duration_category() == "medium"

        # Long (>60 min)
        long_event = CalendarEvent(
            event_id="long",
            subject="Long Meeting",
            organizer_email="organizer@example.com",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
        )
        assert long_event.get_duration_category() == "long"

    def test_meeting_category_classification(self):
        """Test meeting category classification."""
        test_cases = [
            ("Daily Standup", MeetingCategory.STATUS_UPDATE),
            ("Sprint Planning", MeetingCategory.PLANNING),
            ("Code Review", MeetingCategory.REVIEW),
            ("Brainstorm Session", MeetingCategory.BRAINSTORM),
            ("Interview - Senior Engineer", MeetingCategory.INTERVIEW),
            ("Client Demo", MeetingCategory.CLIENT_MEETING),
            ("Happy Hour", MeetingCategory.SOCIAL),
            ("Random Meeting", MeetingCategory.OTHER),
        ]

        for subject, expected_category in test_cases:
            event = CalendarEvent(
                event_id=f"test_{subject}",
                subject=subject,
                organizer_email="organizer@example.com",
                start_time=datetime(2024, 1, 15, 10, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            )
            assert event.classify_meeting_category() == expected_category, f"Failed for subject: {subject}"


class TestEmployee:
    """Tests for Employee model."""

    def test_employee_creation(self):
        """Test basic employee creation."""
        employee = Employee(
            employee_id="EMP001",
            email="john.doe@example.com",
            name="John Doe",
            job_title="Software Engineer",
            job_level=JobLevel.SENIOR_IC,
            job_function=JobFunction.ENGINEERING,
        )

        assert employee.first_name == "John"
        assert employee.last_name == "Doe"
        assert employee.company_domain == "example.com"

    def test_manager_detection(self):
        """Test manager detection."""
        manager = Employee(
            employee_id="MGR001",
            email="manager@example.com",
            name="Manager Name",
            is_manager=True,
            direct_reports=["report1@example.com", "report2@example.com"],
        )

        assert manager.is_people_manager is True
        assert manager.direct_report_count == 2


class TestOrganization:
    """Tests for Organization model."""

    def test_organization_structure(self):
        """Test organization structure and relationships."""
        org = Organization(
            company_name="Test Corp",
            domain="test.com",
        )

        # Add manager
        manager = Employee(
            employee_id="MGR001",
            email="manager@test.com",
            name="Manager",
            job_level=JobLevel.MANAGER,
        )
        org.add_employee(manager)

        # Add reports
        for i in range(3):
            report = Employee(
                employee_id=f"EMP00{i}",
                email=f"report{i}@test.com",
                name=f"Report {i}",
                manager_email="manager@test.com",
            )
            org.add_employee(report)

        # Test relationships
        assert org.employee_count == 4
        assert org.is_internal_email("report0@test.com") is True
        assert org.is_internal_email("external@other.com") is False

        # Test getting direct reports
        reports = org.get_direct_reports("manager@test.com")
        assert len(reports) == 3
