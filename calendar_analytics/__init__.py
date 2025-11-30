"""
Calendar Analytics Module

A comprehensive analytics platform for analyzing Outlook 365 calendar data
combined with HRIS organizational data to generate actionable meeting insights.
"""

__version__ = "1.0.0"
__author__ = "Calendar Analytics Team"

from .models.calendar_event import CalendarEvent
from .models.employee import Employee, Organization
from .analytics.meeting_analyzer import MeetingAnalyzer
from .analytics.insights_engine import InsightsEngine

__all__ = [
    "CalendarEvent",
    "Employee",
    "Organization",
    "MeetingAnalyzer",
    "InsightsEngine",
]
