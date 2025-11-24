"""Tests for analytics modules."""

import pytest
from datetime import datetime, timedelta

from calendar_analytics.models.calendar_event import CalendarEvent, Attendee
from calendar_analytics.models.employee import Employee, Organization, JobLevel, JobFunction
from calendar_analytics.analytics.meeting_analyzer import MeetingAnalyzer
from calendar_analytics.utils.sample_data_generator import SampleDataGenerator


class TestMeetingAnalyzer:
    """Tests for MeetingAnalyzer."""

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        events = []
        base_date = datetime(2024, 1, 15)

        # Small short meeting (1:1, 30 min)
        events.append(CalendarEvent(
            event_id="ss1",
            subject="1:1 Meeting",
            organizer_email="manager@example.com",
            start_time=base_date.replace(hour=9),
            end_time=base_date.replace(hour=9, minute=30),
            attendees=[Attendee(email="report@example.com")],
            is_recurring=True,
        ))

        # Medium medium meeting (team, 60 min)
        events.append(CalendarEvent(
            event_id="mm1",
            subject="Team Standup",
            organizer_email="manager@example.com",
            start_time=base_date.replace(hour=10),
            end_time=base_date.replace(hour=11),
            attendees=[
                Attendee(email=f"team{i}@example.com")
                for i in range(4)
            ],
            is_recurring=True,
        ))

        # Large long meeting (all-hands, 90 min)
        events.append(CalendarEvent(
            event_id="ll1",
            subject="All Hands",
            organizer_email="ceo@example.com",
            start_time=base_date.replace(hour=14),
            end_time=base_date.replace(hour=15, minute=30),
            attendees=[
                Attendee(email=f"emp{i}@example.com")
                for i in range(20)
            ],
            is_recurring=False,
        ))

        return events

    def test_size_duration_matrix(self, sample_events):
        """Test size-duration matrix analysis."""
        analyzer = MeetingAnalyzer()
        matrix = analyzer.analyze_size_duration_matrix(sample_events)

        assert matrix.small_short == 1  # 1:1 meeting
        assert matrix.medium_medium == 1  # team meeting
        assert matrix.large_long == 1  # all-hands
        assert matrix.total_meetings == 3

    def test_recurring_vs_adhoc(self, sample_events):
        """Test recurring vs ad-hoc analysis."""
        analyzer = MeetingAnalyzer()
        result = analyzer.analyze_recurring_vs_adhoc(sample_events)

        assert result["recurring"]["count"] == 2
        assert result["adhoc"]["count"] == 1
        assert result["recurring_percentage"] == pytest.approx(66.7, rel=0.1)

    def test_one_on_one_vs_team(self, sample_events):
        """Test 1:1 vs team meeting analysis."""
        analyzer = MeetingAnalyzer()
        result = analyzer.analyze_one_on_one_vs_team(sample_events)

        assert result["1:1"]["count"] == 1
        assert result["small_team"]["count"] == 1
        assert result["all_hands"]["count"] == 1


class TestSampleDataGenerator:
    """Tests for sample data generator."""

    def test_organization_generation(self):
        """Test organization generation."""
        generator = SampleDataGenerator(company_domain="test.com", seed=42)
        org = generator.generate_organization(employee_count=20)

        assert org.employee_count >= 15  # At least 15 employees
        assert org.domain == "test.com"
        assert len(org.get_all_managers()) > 0

    def test_calendar_generation(self):
        """Test calendar event generation."""
        generator = SampleDataGenerator(company_domain="test.com", seed=42)
        org = generator.generate_organization(employee_count=10)
        calendars = generator.generate_calendar_events(org, days=5)

        # Should have calendars for each employee
        assert len(calendars) == len(org.employees)

        # Should have some events
        total_events = sum(len(events) for events in calendars.values())
        assert total_events > 0

    def test_reproducibility(self):
        """Test that seeded generation is reproducible."""
        gen1 = SampleDataGenerator(seed=123)
        gen2 = SampleDataGenerator(seed=123)

        org1 = gen1.generate_organization(employee_count=10)
        org2 = gen2.generate_organization(employee_count=10)

        # Same employees should be generated
        emails1 = set(org1.employees.keys())
        emails2 = set(org2.employees.keys())

        assert emails1 == emails2
