"""Sample data generator for testing and demonstration."""

import random
from datetime import datetime, timedelta
from typing import Optional
import json

from ..models.calendar_event import CalendarEvent, Attendee, AttendeeResponse
from ..models.employee import Employee, Organization, JobLevel, JobFunction


class SampleDataGenerator:
    """
    Generates realistic sample data for calendar analytics testing.

    Creates:
    - Sample organization with hierarchies
    - Realistic calendar events
    - Various meeting types and patterns
    """

    # Sample names
    FIRST_NAMES = [
        "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah",
        "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nina", "Oscar", "Patricia",
        "Quinn", "Rachel", "Samuel", "Teresa", "Uma", "Victor", "Wendy", "Xavier",
        "Yolanda", "Zachary", "Amir", "Bianca", "Carlos", "Deepa", "Elena", "Feng"
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson",
        "Martin", "Lee", "Perez", "Thompson", "White", "Chen", "Patel", "Kim", "Singh"
    ]

    # Meeting subject templates by category
    MEETING_TEMPLATES = {
        "sprint": [
            "Sprint Planning - {team}",
            "{team} Daily Standup",
            "Sprint Retrospective",
            "Backlog Grooming",
            "Sprint Review - {project}",
        ],
        "one_on_one": [
            "1:1 with {name}",
            "{name} / {name2} Sync",
            "Weekly 1:1",
            "Career Development Chat",
            "Check-in with {name}",
        ],
        "project": [
            "{project} Kickoff",
            "{project} Status Update",
            "{project} Design Review",
            "{project} Technical Discussion",
            "Review {project} Requirements",
        ],
        "team": [
            "{team} Team Meeting",
            "{team} All Hands",
            "Weekly Team Sync - {team}",
            "{team} Planning Session",
        ],
        "client": [
            "Client Call - {client}",
            "{client} Demo",
            "{client} QBR",
            "Sales Pitch - {client}",
            "{client} Contract Review",
        ],
        "interview": [
            "Interview - {role}",
            "Phone Screen - {name}",
            "Technical Interview",
            "Hiring Debrief",
            "Candidate Assessment",
        ],
        "misc": [
            "Meeting",
            "Quick Sync",
            "Discussion",
            "Call",
            "Touchbase",
        ],
    }

    PROJECTS = ["Atlas", "Beacon", "Catalyst", "Delta", "Echo", "Falcon", "Griffin"]
    CLIENTS = ["Acme Corp", "TechStart Inc", "Global Industries", "Digital Solutions", "Innovation Labs"]
    TEAMS = ["Platform", "Product", "Growth", "Infrastructure", "Mobile", "Data", "Security"]
    ROLES = ["Senior Engineer", "Product Manager", "Designer", "Data Scientist", "Engineering Manager"]

    def __init__(self, company_domain: str = "example.com", seed: Optional[int] = None):
        """
        Initialize the generator.

        Args:
            company_domain: Email domain for the company
            seed: Random seed for reproducibility
        """
        self.company_domain = company_domain
        if seed is not None:
            random.seed(seed)

    def generate_organization(
        self,
        employee_count: int = 50,
        company_name: str = "Example Corp"
    ) -> Organization:
        """
        Generate a sample organization with realistic hierarchy.

        Args:
            employee_count: Number of employees to generate
            company_name: Name of the company

        Returns:
            Organization with employees and relationships
        """
        org = Organization(
            company_name=company_name,
            domain=self.company_domain,
        )

        # Generate executives first
        ceo = self._create_employee("ceo", JobLevel.C_LEVEL, JobFunction.EXECUTIVE, None)
        org.add_employee(ceo)

        # Department heads
        functions = [
            JobFunction.ENGINEERING,
            JobFunction.PRODUCT,
            JobFunction.SALES,
            JobFunction.MARKETING,
            JobFunction.HR,
        ]

        dept_heads = []
        for func in functions:
            head = self._create_employee(
                f"head_{func.value.lower()}",
                JobLevel.VP,
                func,
                ceo.email
            )
            org.add_employee(head)
            dept_heads.append(head)

        # Generate remaining employees
        remaining = employee_count - len(org.employees)
        employees_per_dept = remaining // len(dept_heads)

        for dept_head in dept_heads:
            # Create managers
            manager_count = max(1, employees_per_dept // 6)
            managers = []

            for i in range(manager_count):
                manager = self._create_employee(
                    f"manager_{dept_head.job_function.value.lower()}_{i}",
                    JobLevel.MANAGER,
                    dept_head.job_function,
                    dept_head.email
                )
                org.add_employee(manager)
                managers.append(manager)

            # Create ICs under managers
            ics_per_manager = (employees_per_dept - manager_count) // max(manager_count, 1)

            for manager in managers:
                for i in range(ics_per_manager):
                    level = random.choice([JobLevel.INDIVIDUAL_CONTRIBUTOR, JobLevel.SENIOR_IC])
                    ic = self._create_employee(
                        f"ic_{manager.email.split('@')[0]}_{i}",
                        level,
                        manager.job_function,
                        manager.email
                    )
                    org.add_employee(ic)

        # Build relationships
        for employee in org.employees.values():
            if employee.manager_email:
                manager = org.get_employee(employee.manager_email)
                if manager:
                    manager.direct_reports.append(employee.email)
                    manager.is_manager = True

                    # Set skip-level
                    if manager.manager_email:
                        employee.skip_level_manager_email = manager.manager_email

        return org

    def _create_employee(
        self,
        identifier: str,
        level: JobLevel,
        function: JobFunction,
        manager_email: Optional[str]
    ) -> Employee:
        """Create a single employee."""
        first_name = random.choice(self.FIRST_NAMES)
        last_name = random.choice(self.LAST_NAMES)
        name = f"{first_name} {last_name}"

        email = f"{first_name.lower()}.{last_name.lower()}@{self.company_domain}"

        # Generate title based on level and function
        level_prefix = {
            JobLevel.INDIVIDUAL_CONTRIBUTOR: "",
            JobLevel.SENIOR_IC: "Senior ",
            JobLevel.LEAD: "Lead ",
            JobLevel.MANAGER: "",
            JobLevel.SENIOR_MANAGER: "Senior ",
            JobLevel.DIRECTOR: "",
            JobLevel.VP: "VP of ",
            JobLevel.C_LEVEL: "Chief ",
        }

        function_title = {
            JobFunction.ENGINEERING: "Software Engineer" if level in [JobLevel.INDIVIDUAL_CONTRIBUTOR, JobLevel.SENIOR_IC, JobLevel.LEAD] else "Engineering Manager",
            JobFunction.PRODUCT: "Product Manager",
            JobFunction.DESIGN: "Designer",
            JobFunction.SALES: "Sales Representative" if level == JobLevel.INDIVIDUAL_CONTRIBUTOR else "Sales Manager",
            JobFunction.MARKETING: "Marketing Specialist" if level == JobLevel.INDIVIDUAL_CONTRIBUTOR else "Marketing Manager",
            JobFunction.HR: "HR Specialist" if level == JobLevel.INDIVIDUAL_CONTRIBUTOR else "HR Manager",
            JobFunction.EXECUTIVE: "Executive",
        }

        prefix = level_prefix.get(level, "")
        base_title = function_title.get(function, function.value)

        if level == JobLevel.VP:
            title = f"VP of {function.value}"
        elif level == JobLevel.C_LEVEL:
            title = f"Chief {function.value} Officer"
        else:
            title = f"{prefix}{base_title}"

        return Employee(
            employee_id=f"EMP{hash(email) % 10000:04d}",
            email=email,
            name=name,
            job_title=title,
            job_level=level,
            job_function=function,
            department=function.value,
            team=random.choice(self.TEAMS) if function == JobFunction.ENGINEERING else function.value,
            location=random.choice(["San Francisco", "New York", "London", "Remote"]),
            manager_email=manager_email,
            company_domain=self.company_domain,
        )

    def generate_calendar_events(
        self,
        organization: Organization,
        days: int = 30,
        start_date: Optional[datetime] = None,
        events_per_person_per_day: float = 4.5
    ) -> dict[str, list[CalendarEvent]]:
        """
        Generate realistic calendar events for all employees.

        Args:
            organization: Organization to generate events for
            days: Number of days to generate
            start_date: Starting date (defaults to today - days)
            events_per_person_per_day: Average meetings per person per day

        Returns:
            Dictionary mapping email to list of events
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)

        calendars: dict[str, list[CalendarEvent]] = {
            email: [] for email in organization.employees
        }

        employees = list(organization.employees.values())

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)

            # Skip weekends
            if current_date.weekday() >= 5:
                continue

            for employee in employees:
                # Generate events for this person on this day
                num_events = int(random.gauss(events_per_person_per_day, 1.5))
                num_events = max(0, min(8, num_events))

                for _ in range(num_events):
                    event = self._generate_event(
                        organization,
                        employee,
                        current_date,
                    )
                    if event:
                        # Add to all participants' calendars
                        for attendee_email in event.get_attendee_emails():
                            if attendee_email in calendars:
                                calendars[attendee_email].append(event)

        return calendars

    def _generate_event(
        self,
        org: Organization,
        organizer: Employee,
        date: datetime,
    ) -> Optional[CalendarEvent]:
        """Generate a single calendar event."""
        # Determine meeting type
        meeting_type = random.choices(
            ["one_on_one", "team", "project", "sprint", "client", "interview", "misc"],
            weights=[30, 20, 20, 15, 8, 5, 2],
        )[0]

        # Determine time
        hour = random.choices(
            list(range(8, 19)),
            weights=[1, 5, 8, 10, 10, 6, 8, 10, 10, 8, 4],  # Peak at 10-11am and 2-4pm
        )[0]

        # Determine duration
        duration_weights = {
            "one_on_one": [15, 30, 45, 60],
            "team": [30, 60, 90],
            "project": [30, 60],
            "sprint": [15, 60, 90, 120],
            "client": [30, 60],
            "interview": [45, 60],
            "misc": [15, 30],
        }
        duration = random.choice(duration_weights.get(meeting_type, [30, 60]))

        start_time = date.replace(hour=hour, minute=random.choice([0, 30]), second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=duration)

        # Generate attendees based on meeting type
        attendees = self._generate_attendees(org, organizer, meeting_type)

        if not attendees:
            return None

        # Generate subject
        subject = self._generate_subject(meeting_type, org, organizer, attendees)

        # Determine if recurring
        is_recurring = meeting_type in ["one_on_one", "team", "sprint"] and random.random() < 0.7

        event = CalendarEvent(
            event_id=f"evt_{hash(subject + str(start_time))}",
            subject=subject,
            organizer_email=organizer.email,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            is_recurring=is_recurring,
            recurrence_pattern="weekly" if is_recurring else None,
            importance=random.choice(["normal", "normal", "normal", "high"]),
        )

        return event

    def _generate_attendees(
        self,
        org: Organization,
        organizer: Employee,
        meeting_type: str
    ) -> list[Attendee]:
        """Generate appropriate attendees based on meeting type."""
        attendees = []
        employees = list(org.employees.values())

        if meeting_type == "one_on_one":
            # 1:1 with direct report, manager, or peer
            candidates = []
            if organizer.is_people_manager:
                candidates = org.get_direct_reports(organizer.email)
            if organizer.manager_email:
                manager = org.get_employee(organizer.manager_email)
                if manager:
                    candidates.append(manager)
            # Add peers
            candidates.extend([
                e for e in employees
                if e.team == organizer.team and e.email != organizer.email
            ][:5])

            if candidates:
                attendee_emp = random.choice(candidates)
                attendees.append(Attendee(
                    email=attendee_emp.email,
                    name=attendee_emp.name,
                    response=random.choice([AttendeeResponse.ACCEPTED, AttendeeResponse.ACCEPTED, AttendeeResponse.TENTATIVE]),
                ))

        elif meeting_type == "team":
            # Team meeting with 3-8 people from same team/function
            team_members = [
                e for e in employees
                if e.team == organizer.team and e.email != organizer.email
            ]
            num_attendees = min(len(team_members), random.randint(3, 8))
            for emp in random.sample(team_members, num_attendees) if team_members else []:
                attendees.append(Attendee(
                    email=emp.email,
                    name=emp.name,
                    response=random.choice([AttendeeResponse.ACCEPTED, AttendeeResponse.ACCEPTED, AttendeeResponse.NO_RESPONSE]),
                ))

        elif meeting_type in ["project", "sprint"]:
            # Cross-functional meeting
            num_attendees = random.randint(3, 7)
            sampled = random.sample(employees, min(len(employees), num_attendees + 5))
            for emp in sampled[:num_attendees]:
                if emp.email != organizer.email:
                    attendees.append(Attendee(
                        email=emp.email,
                        name=emp.name,
                        response=random.choice([AttendeeResponse.ACCEPTED, AttendeeResponse.TENTATIVE, AttendeeResponse.NO_RESPONSE]),
                    ))

        elif meeting_type == "client":
            # Meeting with external attendee
            client = random.choice(self.CLIENTS)
            attendees.append(Attendee(
                email=f"contact@{client.lower().replace(' ', '')}.com",
                name=f"{random.choice(self.FIRST_NAMES)} from {client}",
                response=AttendeeResponse.ACCEPTED,
                is_external=True,
            ))
            # Add 1-2 internal people
            for emp in random.sample(employees, min(2, len(employees))):
                if emp.email != organizer.email:
                    attendees.append(Attendee(
                        email=emp.email,
                        name=emp.name,
                        response=AttendeeResponse.ACCEPTED,
                    ))

        elif meeting_type == "interview":
            # Interview panel
            attendees.append(Attendee(
                email=f"candidate_{random.randint(100, 999)}@email.com",
                name=f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}",
                response=AttendeeResponse.ACCEPTED,
                is_external=True,
            ))

        else:
            # Misc meeting
            num = random.randint(1, 4)
            for emp in random.sample(employees, min(num, len(employees))):
                if emp.email != organizer.email:
                    attendees.append(Attendee(
                        email=emp.email,
                        name=emp.name,
                        response=AttendeeResponse.ACCEPTED,
                    ))

        return attendees

    def _generate_subject(
        self,
        meeting_type: str,
        org: Organization,
        organizer: Employee,
        attendees: list[Attendee]
    ) -> str:
        """Generate a realistic meeting subject."""
        templates = self.MEETING_TEMPLATES.get(meeting_type, self.MEETING_TEMPLATES["misc"])
        template = random.choice(templates)

        # Fill in placeholders
        subject = template.format(
            team=organizer.team or random.choice(self.TEAMS),
            project=random.choice(self.PROJECTS),
            client=random.choice(self.CLIENTS),
            name=attendees[0].name.split()[0] if attendees else "Someone",
            name2=organizer.name.split()[0],
            role=random.choice(self.ROLES),
        )

        return subject

    def export_sample_data(
        self,
        organization: Organization,
        calendars: dict[str, list[CalendarEvent]],
        output_dir: str
    ) -> None:
        """
        Export sample data to JSON files.

        Args:
            organization: Organization data
            calendars: Calendar events by employee
            output_dir: Directory to write files
        """
        import os

        os.makedirs(output_dir, exist_ok=True)

        # Export organization/HRIS data
        hris_data = {
            "company_name": organization.company_name,
            "domain": organization.domain,
            "employees": [
                {
                    "employee_id": emp.employee_id,
                    "email": emp.email,
                    "name": emp.name,
                    "job_title": emp.job_title,
                    "level": emp.job_level.value,
                    "function": emp.job_function.value,
                    "department": emp.department,
                    "team": emp.team,
                    "location": emp.location,
                    "manager_email": emp.manager_email,
                    "skip_level_manager_email": emp.skip_level_manager_email,
                    "is_manager": emp.is_manager,
                    "direct_reports": emp.direct_reports,
                }
                for emp in organization.employees.values()
            ]
        }

        with open(f"{output_dir}/hris_data.json", "w") as f:
            json.dump(hris_data, f, indent=2)

        # Export calendar data (one file per person)
        calendar_dir = f"{output_dir}/calendars"
        os.makedirs(calendar_dir, exist_ok=True)

        for email, events in calendars.items():
            safe_email = email.replace("@", "_at_").replace(".", "_")
            calendar_data = [
                {
                    "event_id": e.event_id,
                    "subject": e.subject,
                    "organizer_email": e.organizer_email,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "attendees": [
                        {
                            "email": a.email,
                            "name": a.name,
                            "response": a.response.value,
                            "is_required": a.is_required,
                            "is_external": a.is_external,
                        }
                        for a in e.attendees
                    ],
                    "is_recurring": e.is_recurring,
                    "recurrence_pattern": e.recurrence_pattern,
                    "importance": e.importance,
                }
                for e in events
            ]

            with open(f"{calendar_dir}/{safe_email}.json", "w") as f:
                json.dump(calendar_data, f, indent=2)

        print(f"Exported data to {output_dir}/")
        print(f"  - HRIS data: hris_data.json ({len(organization.employees)} employees)")
        print(f"  - Calendars: {len(calendars)} files in calendars/")
