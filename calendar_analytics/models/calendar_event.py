"""Calendar event data models."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import re


class AttendeeResponse(Enum):
    """Attendee response status."""
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NO_RESPONSE = "none"
    ORGANIZER = "organizer"


class MeetingType(Enum):
    """Classification of meeting types."""
    ONE_ON_ONE = "1:1"
    SMALL_TEAM = "small_team"  # 3-5 people
    LARGE_TEAM = "large_team"  # 6-10 people
    ALL_HANDS = "all_hands"  # 11+ people
    EXTERNAL = "external"
    FOCUS_TIME = "focus_time"
    UNKNOWN = "unknown"


class MeetingCategory(Enum):
    """Meeting category based on content/purpose."""
    STATUS_UPDATE = "status_update"
    PLANNING = "planning"
    REVIEW = "review"
    BRAINSTORM = "brainstorm"
    DECISION = "decision"
    TRAINING = "training"
    SOCIAL = "social"
    CLIENT_MEETING = "client_meeting"
    INTERVIEW = "interview"
    PERFORMANCE = "performance"
    PROJECT = "project"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    OTHER = "other"


@dataclass
class Attendee:
    """Meeting attendee information."""
    email: str
    name: str = ""
    response: AttendeeResponse = AttendeeResponse.NO_RESPONSE
    is_required: bool = True
    is_organizer: bool = False
    is_external: bool = False

    def __post_init__(self):
        if not self.name:
            self.name = self.email.split("@")[0].replace(".", " ").title()


@dataclass
class CalendarEvent:
    """Represents a calendar event from Outlook 365."""

    event_id: str
    subject: str
    organizer_email: str
    start_time: datetime
    end_time: datetime
    attendees: list[Attendee] = field(default_factory=list)
    location: str = ""
    body: str = ""
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    is_cancelled: bool = False
    is_all_day: bool = False
    sensitivity: str = "normal"  # normal, personal, private, confidential
    show_as: str = "busy"  # free, tentative, busy, oof, workingElsewhere
    categories: list[str] = field(default_factory=list)
    importance: str = "normal"  # low, normal, high
    response_status: AttendeeResponse = AttendeeResponse.NO_RESPONSE
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    series_master_id: Optional[str] = None
    online_meeting_url: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate meeting duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        """Calculate meeting duration in hours."""
        return self.duration_minutes / 60

    @property
    def attendee_count(self) -> int:
        """Count of attendees including organizer."""
        return len(self.attendees) + 1  # +1 for organizer

    @property
    def accepted_attendee_count(self) -> int:
        """Count of attendees who accepted."""
        return sum(1 for a in self.attendees
                   if a.response == AttendeeResponse.ACCEPTED) + 1

    @property
    def external_attendee_count(self) -> int:
        """Count of external attendees."""
        return sum(1 for a in self.attendees if a.is_external)

    @property
    def internal_attendee_count(self) -> int:
        """Count of internal attendees."""
        return sum(1 for a in self.attendees if not a.is_external) + 1

    @property
    def has_external_attendees(self) -> bool:
        """Check if meeting has external attendees."""
        return self.external_attendee_count > 0

    @property
    def is_one_on_one(self) -> bool:
        """Check if this is a 1:1 meeting."""
        return self.attendee_count == 2

    @property
    def day_of_week(self) -> str:
        """Get day of week for the meeting."""
        return self.start_time.strftime("%A")

    @property
    def hour_of_day(self) -> int:
        """Get hour of day when meeting starts."""
        return self.start_time.hour

    @property
    def is_early_morning(self) -> bool:
        """Meeting before 9 AM."""
        return self.hour_of_day < 9

    @property
    def is_late_evening(self) -> bool:
        """Meeting after 6 PM."""
        return self.hour_of_day >= 18

    @property
    def is_lunch_time(self) -> bool:
        """Meeting during lunch (12-1 PM)."""
        return 12 <= self.hour_of_day < 13

    def get_size_category(self) -> str:
        """Categorize meeting by size."""
        count = self.attendee_count
        if count <= 2:
            return "small"  # 1:1 or solo
        elif count <= 5:
            return "medium"
        else:
            return "large"

    def get_duration_category(self) -> str:
        """Categorize meeting by duration."""
        duration = self.duration_minutes
        if duration <= 30:
            return "short"
        elif duration <= 60:
            return "medium"
        else:
            return "long"

    def get_meeting_type(self) -> MeetingType:
        """Determine the meeting type."""
        if self.has_external_attendees:
            return MeetingType.EXTERNAL

        count = self.attendee_count
        if count == 2:
            return MeetingType.ONE_ON_ONE
        elif count <= 5:
            return MeetingType.SMALL_TEAM
        elif count <= 10:
            return MeetingType.LARGE_TEAM
        else:
            return MeetingType.ALL_HANDS

    def classify_meeting_category(self) -> MeetingCategory:
        """Classify meeting based on subject and body text."""
        text = f"{self.subject} {self.body}".lower()

        # Keywords for classification
        patterns = {
            MeetingCategory.STATUS_UPDATE: r"(status|standup|stand-up|sync|check-in|check in|weekly|daily)",
            MeetingCategory.PLANNING: r"(planning|plan|roadmap|sprint|backlog|quarterly)",
            MeetingCategory.REVIEW: r"(review|retrospective|retro|post-mortem|postmortem|feedback)",
            MeetingCategory.BRAINSTORM: r"(brainstorm|ideation|workshop|design thinking|whiteboard)",
            MeetingCategory.DECISION: r"(decision|approve|approval|sign-off|signoff|go/no-go)",
            MeetingCategory.TRAINING: r"(training|onboarding|learning|tutorial|demo|demonstration)",
            MeetingCategory.SOCIAL: r"(happy hour|team building|celebration|birthday|farewell|lunch|coffee)",
            MeetingCategory.CLIENT_MEETING: r"(client|customer|sales call|pitch|proposal|demo)",
            MeetingCategory.INTERVIEW: r"(interview|hiring|candidate|recruitment)",
            MeetingCategory.PERFORMANCE: r"(performance|1:1|one-on-one|career|growth|development)",
            MeetingCategory.PROJECT: r"(project|kickoff|kick-off|milestone|deliverable)",
            MeetingCategory.OPERATIONAL: r"(ops|operational|incident|outage|on-call|support)",
            MeetingCategory.STRATEGIC: r"(strategy|strategic|vision|leadership|exec|board)",
        }

        for category, pattern in patterns.items():
            if re.search(pattern, text):
                return category

        return MeetingCategory.OTHER

    def get_attendee_emails(self) -> list[str]:
        """Get list of all attendee emails including organizer."""
        emails = [a.email for a in self.attendees]
        if self.organizer_email not in emails:
            emails.append(self.organizer_email)
        return emails

    def has_attendee(self, email: str) -> bool:
        """Check if a specific email is an attendee."""
        return email.lower() in [e.lower() for e in self.get_attendee_emails()]

    def is_organizer(self, email: str) -> bool:
        """Check if email is the organizer."""
        return self.organizer_email.lower() == email.lower()

    def get_response_rate(self) -> float:
        """Calculate response rate (accepted + declined / total)."""
        if not self.attendees:
            return 1.0

        responded = sum(1 for a in self.attendees
                       if a.response in [AttendeeResponse.ACCEPTED,
                                         AttendeeResponse.DECLINED,
                                         AttendeeResponse.TENTATIVE])
        return responded / len(self.attendees)

    def get_acceptance_rate(self) -> float:
        """Calculate acceptance rate."""
        if not self.attendees:
            return 1.0

        accepted = sum(1 for a in self.attendees
                      if a.response == AttendeeResponse.ACCEPTED)
        return accepted / len(self.attendees)

    def __repr__(self) -> str:
        return f"CalendarEvent(subject='{self.subject}', start={self.start_time}, attendees={self.attendee_count})"
