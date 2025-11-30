"""Employee and organization data models for HRIS integration."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class JobLevel(Enum):
    """Employee job levels."""
    INDIVIDUAL_CONTRIBUTOR = "IC"
    SENIOR_IC = "Senior IC"
    LEAD = "Lead"
    MANAGER = "Manager"
    SENIOR_MANAGER = "Senior Manager"
    DIRECTOR = "Director"
    SENIOR_DIRECTOR = "Senior Director"
    VP = "VP"
    SVP = "SVP"
    C_LEVEL = "C-Level"
    UNKNOWN = "Unknown"


class JobFunction(Enum):
    """Job function categories."""
    ENGINEERING = "Engineering"
    PRODUCT = "Product"
    DESIGN = "Design"
    DATA_SCIENCE = "Data Science"
    SALES = "Sales"
    MARKETING = "Marketing"
    CUSTOMER_SUCCESS = "Customer Success"
    OPERATIONS = "Operations"
    HR = "Human Resources"
    FINANCE = "Finance"
    LEGAL = "Legal"
    IT = "IT"
    EXECUTIVE = "Executive"
    ADMIN = "Admin"
    OTHER = "Other"


@dataclass
class Employee:
    """Represents an employee from HRIS data."""

    employee_id: str
    email: str
    name: str
    job_title: str = ""
    job_level: JobLevel = JobLevel.UNKNOWN
    job_function: JobFunction = JobFunction.OTHER
    department: str = ""
    team: str = ""
    location: str = ""
    manager_email: Optional[str] = None
    skip_level_manager_email: Optional[str] = None
    hire_date: Optional[str] = None
    is_manager: bool = False
    is_active: bool = True
    direct_reports: list[str] = field(default_factory=list)  # List of emails
    cost_center: str = ""
    division: str = ""
    company_domain: str = ""

    def __post_init__(self):
        """Extract company domain from email if not provided."""
        if not self.company_domain and "@" in self.email:
            self.company_domain = self.email.split("@")[1].lower()

    @property
    def direct_report_count(self) -> int:
        """Number of direct reports."""
        return len(self.direct_reports)

    @property
    def is_people_manager(self) -> bool:
        """Check if employee manages people."""
        return self.direct_report_count > 0 or self.is_manager

    @property
    def first_name(self) -> str:
        """Get first name."""
        return self.name.split()[0] if self.name else ""

    @property
    def last_name(self) -> str:
        """Get last name."""
        parts = self.name.split()
        return parts[-1] if len(parts) > 1 else ""

    def is_same_team(self, other: "Employee") -> bool:
        """Check if two employees are on the same team."""
        return self.team == other.team and self.team != ""

    def is_same_department(self, other: "Employee") -> bool:
        """Check if two employees are in the same department."""
        return self.department == other.department and self.department != ""

    def is_same_function(self, other: "Employee") -> bool:
        """Check if two employees have the same job function."""
        return self.job_function == other.job_function

    def reports_to(self, other: "Employee") -> bool:
        """Check if this employee reports to other."""
        return self.manager_email and self.manager_email.lower() == other.email.lower()

    def is_skip_level_of(self, other: "Employee") -> bool:
        """Check if this employee is skip-level manager of other."""
        return other.skip_level_manager_email and other.skip_level_manager_email.lower() == self.email.lower()

    def get_level_numeric(self) -> int:
        """Get numeric level for comparison."""
        level_map = {
            JobLevel.INDIVIDUAL_CONTRIBUTOR: 1,
            JobLevel.SENIOR_IC: 2,
            JobLevel.LEAD: 3,
            JobLevel.MANAGER: 4,
            JobLevel.SENIOR_MANAGER: 5,
            JobLevel.DIRECTOR: 6,
            JobLevel.SENIOR_DIRECTOR: 7,
            JobLevel.VP: 8,
            JobLevel.SVP: 9,
            JobLevel.C_LEVEL: 10,
            JobLevel.UNKNOWN: 0,
        }
        return level_map.get(self.job_level, 0)

    def __repr__(self) -> str:
        return f"Employee(name='{self.name}', email='{self.email}', title='{self.job_title}')"


@dataclass
class Team:
    """Represents a team within the organization."""

    team_id: str
    name: str
    manager_email: str
    members: list[str] = field(default_factory=list)  # List of emails
    department: str = ""
    function: JobFunction = JobFunction.OTHER
    parent_team_id: Optional[str] = None

    @property
    def size(self) -> int:
        """Team size including manager."""
        return len(self.members) + 1


@dataclass
class Organization:
    """Represents the organizational structure."""

    company_name: str
    domain: str
    employees: dict[str, Employee] = field(default_factory=dict)  # email -> Employee
    teams: dict[str, Team] = field(default_factory=dict)  # team_id -> Team

    def add_employee(self, employee: Employee) -> None:
        """Add an employee to the organization."""
        self.employees[employee.email.lower()] = employee

    def get_employee(self, email: str) -> Optional[Employee]:
        """Get employee by email."""
        return self.employees.get(email.lower())

    def get_manager(self, employee: Employee) -> Optional[Employee]:
        """Get the manager of an employee."""
        if employee.manager_email:
            return self.get_employee(employee.manager_email)
        return None

    def get_skip_level_manager(self, employee: Employee) -> Optional[Employee]:
        """Get the skip-level manager of an employee."""
        if employee.skip_level_manager_email:
            return self.get_employee(employee.skip_level_manager_email)

        manager = self.get_manager(employee)
        if manager:
            return self.get_manager(manager)
        return None

    def get_direct_reports(self, manager_email: str) -> list[Employee]:
        """Get all direct reports of a manager."""
        return [emp for emp in self.employees.values()
                if emp.manager_email and emp.manager_email.lower() == manager_email.lower()]

    def get_team_members(self, employee: Employee) -> list[Employee]:
        """Get all members of the same team."""
        return [emp for emp in self.employees.values()
                if emp.team == employee.team and emp.email != employee.email]

    def get_employees_by_function(self, function: JobFunction) -> list[Employee]:
        """Get all employees in a job function."""
        return [emp for emp in self.employees.values()
                if emp.job_function == function]

    def get_employees_by_level(self, level: JobLevel) -> list[Employee]:
        """Get all employees at a job level."""
        return [emp for emp in self.employees.values()
                if emp.job_level == level]

    def get_all_managers(self) -> list[Employee]:
        """Get all employees who are managers."""
        return [emp for emp in self.employees.values()
                if emp.is_people_manager]

    def is_internal_email(self, email: str) -> bool:
        """Check if an email belongs to the organization."""
        if "@" not in email:
            return False
        email_domain = email.split("@")[1].lower()
        return email_domain == self.domain.lower()

    def get_reporting_chain(self, employee: Employee) -> list[Employee]:
        """Get the full reporting chain up to the top."""
        chain = []
        current = employee
        while current.manager_email:
            manager = self.get_employee(current.manager_email)
            if manager and manager not in chain:
                chain.append(manager)
                current = manager
            else:
                break
        return chain

    def get_org_depth(self, employee: Employee) -> int:
        """Get the organizational depth of an employee."""
        return len(self.get_reporting_chain(employee))

    @property
    def employee_count(self) -> int:
        """Total number of employees."""
        return len(self.employees)

    @property
    def manager_count(self) -> int:
        """Total number of managers."""
        return len(self.get_all_managers())

    def get_function_breakdown(self) -> dict[JobFunction, int]:
        """Get count of employees by function."""
        breakdown: dict[JobFunction, int] = {}
        for emp in self.employees.values():
            breakdown[emp.job_function] = breakdown.get(emp.job_function, 0) + 1
        return breakdown

    def get_level_breakdown(self) -> dict[JobLevel, int]:
        """Get count of employees by level."""
        breakdown: dict[JobLevel, int] = {}
        for emp in self.employees.values():
            breakdown[emp.job_level] = breakdown.get(emp.job_level, 0) + 1
        return breakdown

    def __repr__(self) -> str:
        return f"Organization(name='{self.company_name}', employees={self.employee_count})"
