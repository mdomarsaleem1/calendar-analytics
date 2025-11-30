"""Outlook 365 calendar data loader."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.calendar_event import (
    CalendarEvent,
    Attendee,
    AttendeeResponse,
)


class OutlookCalendarLoader:
    """
    Loads calendar data from Outlook 365 exports.

    Supports multiple export formats:
    - CSV export from Outlook
    - JSON export from Microsoft Graph API
    - ICS calendar files
    """

    RESPONSE_MAP = {
        "accepted": AttendeeResponse.ACCEPTED,
        "declined": AttendeeResponse.DECLINED,
        "tentative": AttendeeResponse.TENTATIVE,
        "tentativelyaccepted": AttendeeResponse.TENTATIVE,
        "none": AttendeeResponse.NO_RESPONSE,
        "notresponded": AttendeeResponse.NO_RESPONSE,
        "organizer": AttendeeResponse.ORGANIZER,
    }

    def __init__(self, company_domain: str = ""):
        """
        Initialize the loader.

        Args:
            company_domain: Company email domain for identifying external attendees
        """
        self.company_domain = company_domain.lower()

    def load_csv(self, file_path: str | Path, owner_email: str = "") -> list[CalendarEvent]:
        """
        Load calendar events from Outlook CSV export.

        Args:
            file_path: Path to the CSV file
            owner_email: Email of the calendar owner

        Returns:
            List of CalendarEvent objects
        """
        events = []
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                event = self._parse_csv_row(row, owner_email)
                if event:
                    events.append(event)

        return events

    def _parse_csv_row(self, row: dict, owner_email: str) -> Optional[CalendarEvent]:
        """Parse a single CSV row into a CalendarEvent."""
        try:
            # Handle different CSV column naming conventions
            subject = row.get("Subject", row.get("subject", ""))
            start_date = row.get("Start Date", row.get("start_date", ""))
            start_time = row.get("Start Time", row.get("start_time", ""))
            end_date = row.get("End Date", row.get("end_date", ""))
            end_time = row.get("End Time", row.get("end_time", ""))

            # Parse datetime
            start_str = f"{start_date} {start_time}"
            end_str = f"{end_date} {end_time}"

            # Try multiple datetime formats
            start_dt = self._parse_datetime(start_str)
            end_dt = self._parse_datetime(end_str)

            if not start_dt or not end_dt:
                return None

            # Parse attendees
            attendees_str = row.get("Required Attendees", row.get("attendees", ""))
            optional_str = row.get("Optional Attendees", row.get("optional_attendees", ""))
            organizer = row.get("Organizer", row.get("organizer", owner_email))

            attendees = self._parse_attendees_string(attendees_str, required=True)
            attendees.extend(self._parse_attendees_string(optional_str, required=False))

            # Determine if recurring
            is_recurring = row.get("Recurring", row.get("is_recurring", "")).lower() in ["yes", "true", "1"]
            recurrence = row.get("Recurrence Pattern", row.get("recurrence_pattern", ""))

            # Check if all day
            is_all_day = row.get("All day event", row.get("is_all_day", "")).lower() in ["yes", "true", "1"]

            event = CalendarEvent(
                event_id=row.get("UID", row.get("event_id", f"evt_{hash(subject + str(start_dt))}")),
                subject=subject,
                organizer_email=organizer or owner_email,
                start_time=start_dt,
                end_time=end_dt,
                attendees=attendees,
                location=row.get("Location", row.get("location", "")),
                body=row.get("Description", row.get("body", "")),
                is_recurring=is_recurring,
                recurrence_pattern=recurrence if recurrence else None,
                is_all_day=is_all_day,
                categories=self._parse_categories(row.get("Categories", row.get("categories", ""))),
                importance=row.get("Priority", row.get("importance", "normal")).lower(),
                show_as=row.get("Show As", row.get("show_as", "busy")).lower(),
            )

            return event

        except Exception as e:
            print(f"Error parsing CSV row: {e}")
            return None

    def load_json(self, file_path: str | Path, owner_email: str = "") -> list[CalendarEvent]:
        """
        Load calendar events from Microsoft Graph API JSON export.

        Args:
            file_path: Path to the JSON file
            owner_email: Email of the calendar owner

        Returns:
            List of CalendarEvent objects
        """
        events = []
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both single event and array of events
        event_list = data if isinstance(data, list) else data.get("value", [data])

        for event_data in event_list:
            event = self._parse_graph_event(event_data, owner_email)
            if event:
                events.append(event)

        return events

    def _parse_graph_event(self, data: dict, owner_email: str) -> Optional[CalendarEvent]:
        """Parse a Microsoft Graph API event object."""
        try:
            # Parse start and end times
            start_data = data.get("start", {})
            end_data = data.get("end", {})

            start_str = start_data.get("dateTime", "")
            end_str = end_data.get("dateTime", "")

            start_dt = self._parse_datetime(start_str)
            end_dt = self._parse_datetime(end_str)

            if not start_dt or not end_dt:
                return None

            # Parse attendees
            attendees = []
            for att in data.get("attendees", []):
                email_data = att.get("emailAddress", {})
                email = email_data.get("address", "")
                name = email_data.get("name", "")
                response = att.get("status", {}).get("response", "none")
                att_type = att.get("type", "required")

                attendee = Attendee(
                    email=email,
                    name=name,
                    response=self.RESPONSE_MAP.get(response.lower(), AttendeeResponse.NO_RESPONSE),
                    is_required=att_type.lower() == "required",
                    is_external=self._is_external_email(email),
                )
                attendees.append(attendee)

            # Get organizer
            organizer_data = data.get("organizer", {}).get("emailAddress", {})
            organizer_email = organizer_data.get("address", owner_email)

            # Check for online meeting
            online_meeting = data.get("onlineMeeting", {})
            online_url = online_meeting.get("joinUrl", "") if online_meeting else ""

            event = CalendarEvent(
                event_id=data.get("id", data.get("iCalUId", "")),
                subject=data.get("subject", ""),
                organizer_email=organizer_email,
                start_time=start_dt,
                end_time=end_dt,
                attendees=attendees,
                location=data.get("location", {}).get("displayName", ""),
                body=data.get("body", {}).get("content", ""),
                is_recurring=data.get("recurrence") is not None,
                recurrence_pattern=json.dumps(data.get("recurrence")) if data.get("recurrence") else None,
                is_cancelled=data.get("isCancelled", False),
                is_all_day=data.get("isAllDay", False),
                sensitivity=data.get("sensitivity", "normal").lower(),
                show_as=data.get("showAs", "busy").lower(),
                categories=data.get("categories", []),
                importance=data.get("importance", "normal").lower(),
                created_time=self._parse_datetime(data.get("createdDateTime")),
                modified_time=self._parse_datetime(data.get("lastModifiedDateTime")),
                series_master_id=data.get("seriesMasterId"),
                online_meeting_url=online_url,
            )

            return event

        except Exception as e:
            print(f"Error parsing Graph event: {e}")
            return None

    def load_from_dict(self, data: dict, owner_email: str = "") -> CalendarEvent:
        """
        Create a CalendarEvent from a dictionary.

        Useful for programmatic creation of events.
        """
        attendees = []
        for att_data in data.get("attendees", []):
            if isinstance(att_data, str):
                attendees.append(Attendee(
                    email=att_data,
                    is_external=self._is_external_email(att_data)
                ))
            else:
                attendees.append(Attendee(
                    email=att_data.get("email", ""),
                    name=att_data.get("name", ""),
                    response=self.RESPONSE_MAP.get(
                        att_data.get("response", "none").lower(),
                        AttendeeResponse.NO_RESPONSE
                    ),
                    is_required=att_data.get("is_required", True),
                    is_external=self._is_external_email(att_data.get("email", "")),
                ))

        start_time = data.get("start_time")
        if isinstance(start_time, str):
            start_time = self._parse_datetime(start_time)

        end_time = data.get("end_time")
        if isinstance(end_time, str):
            end_time = self._parse_datetime(end_time)

        return CalendarEvent(
            event_id=data.get("event_id", f"evt_{hash(str(data))}"),
            subject=data.get("subject", ""),
            organizer_email=data.get("organizer_email", owner_email),
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            location=data.get("location", ""),
            body=data.get("body", ""),
            is_recurring=data.get("is_recurring", False),
            recurrence_pattern=data.get("recurrence_pattern"),
            is_cancelled=data.get("is_cancelled", False),
            is_all_day=data.get("is_all_day", False),
            categories=data.get("categories", []),
            importance=data.get("importance", "normal"),
        )

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string in various formats."""
        if not dt_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_attendees_string(self, attendees_str: str, required: bool = True) -> list[Attendee]:
        """Parse attendees from a comma/semicolon-separated string."""
        if not attendees_str:
            return []

        attendees = []
        # Split by common delimiters
        for delimiter in [";", ","]:
            if delimiter in attendees_str:
                parts = attendees_str.split(delimiter)
                break
        else:
            parts = [attendees_str]

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Try to extract email from "Name <email>" format
            if "<" in part and ">" in part:
                name = part[:part.index("<")].strip()
                email = part[part.index("<")+1:part.index(">")].strip()
            elif "@" in part:
                email = part
                name = ""
            else:
                continue

            attendees.append(Attendee(
                email=email,
                name=name,
                is_required=required,
                is_external=self._is_external_email(email),
            ))

        return attendees

    def _parse_categories(self, categories_str: str) -> list[str]:
        """Parse categories from a string."""
        if not categories_str:
            return []

        for delimiter in [";", ","]:
            if delimiter in categories_str:
                return [c.strip() for c in categories_str.split(delimiter) if c.strip()]

        return [categories_str.strip()] if categories_str.strip() else []

    def _is_external_email(self, email: str) -> bool:
        """Check if an email is external to the company."""
        if not self.company_domain or "@" not in email:
            return False

        email_domain = email.split("@")[1].lower()
        return email_domain != self.company_domain

    def load_multiple_calendars(
        self,
        file_paths: dict[str, str | Path],
        file_format: str = "json"
    ) -> dict[str, list[CalendarEvent]]:
        """
        Load calendars for multiple users.

        Args:
            file_paths: Dict mapping email to file path
            file_format: Format of files ("json" or "csv")

        Returns:
            Dict mapping email to list of events
        """
        calendars = {}

        for email, path in file_paths.items():
            if file_format == "json":
                calendars[email] = self.load_json(path, email)
            else:
                calendars[email] = self.load_csv(path, email)

        return calendars
