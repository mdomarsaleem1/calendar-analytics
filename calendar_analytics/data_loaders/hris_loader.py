"""HRIS data loader for organizational information."""

import csv
import json
from pathlib import Path
from typing import Optional

from ..models.employee import (
    Employee,
    Organization,
    Team,
    JobLevel,
    JobFunction,
)


class HRISLoader:
    """
    Loads HRIS (Human Resource Information System) data.

    Supports common HRIS export formats including:
    - CSV exports
    - JSON exports
    - Workday-style exports
    - BambooHR-style exports
    """

    JOB_LEVEL_MAP = {
        # Common level naming conventions
        "ic": JobLevel.INDIVIDUAL_CONTRIBUTOR,
        "individual contributor": JobLevel.INDIVIDUAL_CONTRIBUTOR,
        "associate": JobLevel.INDIVIDUAL_CONTRIBUTOR,
        "junior": JobLevel.INDIVIDUAL_CONTRIBUTOR,
        "entry": JobLevel.INDIVIDUAL_CONTRIBUTOR,
        "senior": JobLevel.SENIOR_IC,
        "senior ic": JobLevel.SENIOR_IC,
        "staff": JobLevel.SENIOR_IC,
        "lead": JobLevel.LEAD,
        "tech lead": JobLevel.LEAD,
        "team lead": JobLevel.LEAD,
        "principal": JobLevel.LEAD,
        "manager": JobLevel.MANAGER,
        "people manager": JobLevel.MANAGER,
        "senior manager": JobLevel.SENIOR_MANAGER,
        "director": JobLevel.DIRECTOR,
        "senior director": JobLevel.SENIOR_DIRECTOR,
        "vp": JobLevel.VP,
        "vice president": JobLevel.VP,
        "svp": JobLevel.SVP,
        "senior vice president": JobLevel.SVP,
        "evp": JobLevel.SVP,
        "c-level": JobLevel.C_LEVEL,
        "ceo": JobLevel.C_LEVEL,
        "cto": JobLevel.C_LEVEL,
        "cfo": JobLevel.C_LEVEL,
        "coo": JobLevel.C_LEVEL,
        "cio": JobLevel.C_LEVEL,
        "cpo": JobLevel.C_LEVEL,
        "chief": JobLevel.C_LEVEL,
    }

    JOB_FUNCTION_MAP = {
        # Common function naming conventions
        "engineering": JobFunction.ENGINEERING,
        "software": JobFunction.ENGINEERING,
        "development": JobFunction.ENGINEERING,
        "tech": JobFunction.ENGINEERING,
        "technology": JobFunction.ENGINEERING,
        "product": JobFunction.PRODUCT,
        "product management": JobFunction.PRODUCT,
        "design": JobFunction.DESIGN,
        "ux": JobFunction.DESIGN,
        "ui": JobFunction.DESIGN,
        "data": JobFunction.DATA_SCIENCE,
        "data science": JobFunction.DATA_SCIENCE,
        "analytics": JobFunction.DATA_SCIENCE,
        "ml": JobFunction.DATA_SCIENCE,
        "machine learning": JobFunction.DATA_SCIENCE,
        "sales": JobFunction.SALES,
        "business development": JobFunction.SALES,
        "account": JobFunction.SALES,
        "marketing": JobFunction.MARKETING,
        "growth": JobFunction.MARKETING,
        "customer success": JobFunction.CUSTOMER_SUCCESS,
        "cs": JobFunction.CUSTOMER_SUCCESS,
        "support": JobFunction.CUSTOMER_SUCCESS,
        "operations": JobFunction.OPERATIONS,
        "ops": JobFunction.OPERATIONS,
        "hr": JobFunction.HR,
        "human resources": JobFunction.HR,
        "people": JobFunction.HR,
        "talent": JobFunction.HR,
        "recruiting": JobFunction.HR,
        "finance": JobFunction.FINANCE,
        "accounting": JobFunction.FINANCE,
        "legal": JobFunction.LEGAL,
        "compliance": JobFunction.LEGAL,
        "it": JobFunction.IT,
        "infrastructure": JobFunction.IT,
        "security": JobFunction.IT,
        "executive": JobFunction.EXECUTIVE,
        "admin": JobFunction.ADMIN,
        "administrative": JobFunction.ADMIN,
    }

    def __init__(self, company_name: str = "", company_domain: str = ""):
        """
        Initialize the loader.

        Args:
            company_name: Name of the company
            company_domain: Email domain of the company
        """
        self.company_name = company_name
        self.company_domain = company_domain.lower()

    def load_csv(self, file_path: str | Path) -> Organization:
        """
        Load organization data from CSV.

        Expected columns (flexible naming):
        - Employee ID
        - Email
        - Name / Full Name
        - Job Title
        - Level
        - Function / Department
        - Team
        - Manager Email
        - Location
        - Hire Date

        Args:
            file_path: Path to the CSV file

        Returns:
            Organization object with all employees
        """
        org = Organization(
            company_name=self.company_name,
            domain=self.company_domain,
        )

        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                employee = self._parse_csv_row(row)
                if employee:
                    org.add_employee(employee)

        # Build manager relationships
        self._build_relationships(org)

        return org

    def _parse_csv_row(self, row: dict) -> Optional[Employee]:
        """Parse a single CSV row into an Employee."""
        try:
            # Flexible column name mapping
            email = self._get_field(row, ["email", "work_email", "corporate_email", "email_address"])
            if not email:
                return None

            name = self._get_field(row, ["name", "full_name", "employee_name", "display_name"])
            employee_id = self._get_field(row, ["employee_id", "id", "emp_id", "worker_id"]) or email

            job_title = self._get_field(row, ["job_title", "title", "position", "role"])
            level_str = self._get_field(row, ["level", "job_level", "grade", "band"])
            function_str = self._get_field(row, [
                "function", "job_function", "department", "dept",
                "business_unit", "org_unit"
            ])

            team = self._get_field(row, ["team", "team_name", "group"])
            manager_email = self._get_field(row, [
                "manager_email", "manager", "reports_to",
                "supervisor_email", "direct_manager"
            ])
            skip_manager = self._get_field(row, [
                "skip_level_manager", "skip_manager", "skip_level",
                "second_level_manager", "grandmanager"
            ])

            location = self._get_field(row, ["location", "office", "site", "work_location"])
            hire_date = self._get_field(row, ["hire_date", "start_date", "join_date"])
            is_manager = self._get_field(row, ["is_manager", "manager_flag", "people_manager"])
            cost_center = self._get_field(row, ["cost_center", "cost_centre"])
            division = self._get_field(row, ["division", "segment"])

            # Parse job level
            job_level = self._parse_job_level(level_str, job_title)

            # Parse job function
            job_function = self._parse_job_function(function_str, job_title)

            # Parse manager flag
            is_manager_bool = str(is_manager).lower() in ["yes", "true", "1", "y"] if is_manager else False

            employee = Employee(
                employee_id=employee_id,
                email=email.lower(),
                name=name or email.split("@")[0].replace(".", " ").title(),
                job_title=job_title or "",
                job_level=job_level,
                job_function=job_function,
                department=function_str or "",
                team=team or "",
                location=location or "",
                manager_email=manager_email.lower() if manager_email else None,
                skip_level_manager_email=skip_manager.lower() if skip_manager else None,
                hire_date=hire_date,
                is_manager=is_manager_bool,
                cost_center=cost_center or "",
                division=division or "",
                company_domain=self.company_domain,
            )

            return employee

        except Exception as e:
            print(f"Error parsing HRIS row: {e}")
            return None

    def load_json(self, file_path: str | Path) -> Organization:
        """
        Load organization data from JSON.

        Args:
            file_path: Path to the JSON file

        Returns:
            Organization object with all employees
        """
        org = Organization(
            company_name=self.company_name,
            domain=self.company_domain,
        )

        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            employees_data = data
        elif "employees" in data:
            employees_data = data["employees"]
        elif "data" in data:
            employees_data = data["data"]
        else:
            employees_data = [data]

        for emp_data in employees_data:
            employee = self._parse_json_employee(emp_data)
            if employee:
                org.add_employee(employee)

        # Build manager relationships
        self._build_relationships(org)

        return org

    def _parse_json_employee(self, data: dict) -> Optional[Employee]:
        """Parse a JSON object into an Employee."""
        try:
            email = data.get("email", data.get("work_email", ""))
            if not email:
                return None

            level_str = data.get("level", data.get("job_level", ""))
            function_str = data.get("function", data.get("department", ""))
            job_title = data.get("job_title", data.get("title", ""))

            employee = Employee(
                employee_id=data.get("employee_id", data.get("id", email)),
                email=email.lower(),
                name=data.get("name", data.get("full_name", "")),
                job_title=job_title,
                job_level=self._parse_job_level(level_str, job_title),
                job_function=self._parse_job_function(function_str, job_title),
                department=function_str,
                team=data.get("team", ""),
                location=data.get("location", ""),
                manager_email=data.get("manager_email", "").lower() or None,
                skip_level_manager_email=data.get("skip_level_manager_email", "").lower() or None,
                hire_date=data.get("hire_date"),
                is_manager=data.get("is_manager", False),
                direct_reports=data.get("direct_reports", []),
                cost_center=data.get("cost_center", ""),
                division=data.get("division", ""),
                company_domain=self.company_domain,
            )

            return employee

        except Exception as e:
            print(f"Error parsing HRIS JSON: {e}")
            return None

    def load_from_dict(self, data: dict) -> Employee:
        """Create an Employee from a dictionary."""
        level_str = data.get("level", data.get("job_level", ""))
        function_str = data.get("function", data.get("department", ""))
        job_title = data.get("job_title", data.get("title", ""))

        return Employee(
            employee_id=data.get("employee_id", data.get("email", "")),
            email=data.get("email", "").lower(),
            name=data.get("name", ""),
            job_title=job_title,
            job_level=self._parse_job_level(level_str, job_title),
            job_function=self._parse_job_function(function_str, job_title),
            department=function_str,
            team=data.get("team", ""),
            location=data.get("location", ""),
            manager_email=data.get("manager_email", "").lower() or None,
            skip_level_manager_email=data.get("skip_level_manager_email", "").lower() or None,
            hire_date=data.get("hire_date"),
            is_manager=data.get("is_manager", False),
            direct_reports=data.get("direct_reports", []),
            cost_center=data.get("cost_center", ""),
            division=data.get("division", ""),
            company_domain=self.company_domain,
        )

    def _get_field(self, row: dict, possible_names: list[str]) -> Optional[str]:
        """Get a field value trying multiple possible column names."""
        for name in possible_names:
            # Try exact match
            if name in row:
                return row[name]
            # Try case-insensitive match
            for key in row:
                if key.lower().replace(" ", "_") == name.lower().replace(" ", "_"):
                    return row[key]
        return None

    def _parse_job_level(self, level_str: Optional[str], job_title: str = "") -> JobLevel:
        """Parse job level from string."""
        if not level_str and not job_title:
            return JobLevel.UNKNOWN

        # Try level string first
        if level_str:
            level_lower = level_str.lower().strip()
            if level_lower in self.JOB_LEVEL_MAP:
                return self.JOB_LEVEL_MAP[level_lower]

            # Try partial match
            for key, value in self.JOB_LEVEL_MAP.items():
                if key in level_lower:
                    return value

        # Try to infer from job title
        if job_title:
            title_lower = job_title.lower()
            for key, value in self.JOB_LEVEL_MAP.items():
                if key in title_lower:
                    return value

        return JobLevel.UNKNOWN

    def _parse_job_function(self, function_str: Optional[str], job_title: str = "") -> JobFunction:
        """Parse job function from string."""
        if not function_str and not job_title:
            return JobFunction.OTHER

        # Try function string first
        if function_str:
            func_lower = function_str.lower().strip()
            if func_lower in self.JOB_FUNCTION_MAP:
                return self.JOB_FUNCTION_MAP[func_lower]

            # Try partial match
            for key, value in self.JOB_FUNCTION_MAP.items():
                if key in func_lower:
                    return value

        # Try to infer from job title
        if job_title:
            title_lower = job_title.lower()
            for key, value in self.JOB_FUNCTION_MAP.items():
                if key in title_lower:
                    return value

        return JobFunction.OTHER

    def _build_relationships(self, org: Organization) -> None:
        """Build manager-report relationships in the organization."""
        # Build direct reports lists
        for employee in org.employees.values():
            if employee.manager_email:
                manager = org.get_employee(employee.manager_email)
                if manager and employee.email not in manager.direct_reports:
                    manager.direct_reports.append(employee.email)
                    manager.is_manager = True

        # Build skip-level relationships if not already set
        for employee in org.employees.values():
            if not employee.skip_level_manager_email and employee.manager_email:
                manager = org.get_employee(employee.manager_email)
                if manager and manager.manager_email:
                    employee.skip_level_manager_email = manager.manager_email

    def create_organization_from_employees(
        self,
        employees: list[dict],
        company_name: str = "",
        company_domain: str = ""
    ) -> Organization:
        """
        Create an Organization from a list of employee dictionaries.

        Args:
            employees: List of employee data dictionaries
            company_name: Company name
            company_domain: Company email domain

        Returns:
            Organization object
        """
        self.company_name = company_name or self.company_name
        self.company_domain = company_domain or self.company_domain

        org = Organization(
            company_name=self.company_name,
            domain=self.company_domain,
        )

        for emp_data in employees:
            employee = self.load_from_dict(emp_data)
            org.add_employee(employee)

        self._build_relationships(org)

        return org
