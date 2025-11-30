# Calendar Analytics Technical Specification

## Platform Overview
Calendar Analytics ingests Outlook 365 calendar data and HRIS metadata to produce actionable meeting insights. The system is designed for notebook-driven workflows (Jupyter) and follows a cookie-cutter style layout with credentials and data artifacts excluded via `.gitignore`.

## Architecture and Components
- **Data loaders**: `calendar_analytics/data_loaders/` for Outlook exports and HRIS sources, with enrichment handled by `data_processor.py`.
- **Analytics engine**: `calendar_analytics/analytics/` modules including meeting, manager, cross-functional, text/NLP, and insights orchestration logic.
- **Models**: Typed entities in `calendar_analytics/models/` representing events and employees.
- **Utilities**: Sample data generation and reporting helpers in `calendar_analytics/utils/` plus CLI entrypoint `calendar_analytics/cli.py`.
- **Interfaces**: CLI commands for demo, data generation, and analysis; Python API for custom workflows; notebooks preferred for end-to-end runs.

```
calendar_analytics/
├── models/               # Core data models
├── data_loaders/         # Ingestion & enrichment
├── analytics/            # Domain analytics modules
├── utils/                # Report generation & sample data
├── cli.py                # CLI surface
└── __init__.py
```

## Detailed Feature Set
- Meeting size/duration matrix, recurring vs ad-hoc breakdowns, 1:1 vs team vs all-hands, manager time patterns, and cross-functional collaboration scores.
- Calendar hygiene: fragmentation, back-to-back detection, buffer gaps, standard duration adoption, and response/acceptance rates.
- Boundary spanners, at-risk manager-report pairs, and collaboration silos across functions and teams.
- Text analytics: topic extraction, keyword surfacing, naming pattern analysis, and sentiment indicators on subjects.
- Cost and effectiveness: estimated meeting costs, customer-facing time, performance best-practice detection, and recommendation generation.

## Installation & Environment
```bash
# Clone and install
pip install -e .

# Include dev extras when contributing
pip install -e ".[dev]"
```
- Use Jupyter notebooks for final analytical scripts; keep credentials/data outputs outside version control (already covered in `.gitignore`).

## CLI Usage
```bash
# Run a demo with generated data
calendar-analytics demo

# Generate sample data
calendar-analytics generate-sample --employees 50 --days 30 --output ./sample_data

# Analyze real data
calendar-analytics analyze \
  --hris ./hris_data.json \
  --calendars ./calendar_exports/ \
  --output ./report.md \
  --format markdown
```

## Data Input Formats
### HRIS JSON
```json
{
  "company_name": "Example Corp",
  "domain": "example.com",
  "employees": [
    {
      "employee_id": "EMP001",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "job_title": "Software Engineer",
      "level": "Senior IC",
      "function": "Engineering",
      "department": "Engineering",
      "team": "Platform",
      "manager_email": "jane.smith@example.com",
      "location": "San Francisco",
      "is_manager": false
    }
  ]
}
```

### HRIS CSV
```csv
employee_id,email,name,job_title,level,function,team,manager_email,location
EMP001,john.doe@example.com,John Doe,Software Engineer,Senior IC,Engineering,Platform,jane.smith@example.com,San Francisco
```

### Outlook Calendar Export (JSON)
```json
[
  {
    "id": "event123",
    "subject": "Weekly Team Sync",
    "start": {"dateTime": "2024-01-15T10:00:00"},
    "end": {"dateTime": "2024-01-15T11:00:00"},
    "organizer": {
      "emailAddress": {"address": "organizer@example.com"}
    },
    "attendees": [
      {
        "emailAddress": {"address": "attendee@example.com", "name": "Attendee Name"},
        "status": {"response": "accepted"},
        "type": "required"
      }
    ],
    "recurrence": {"pattern": {"type": "weekly"}},
    "isAllDay": false
  }
]
```

## Python API Examples
```python
from calendar_analytics import InsightsEngine
from calendar_analytics.data_loaders import HRISLoader, OutlookCalendarLoader
from calendar_analytics.utils import ReportGenerator

# Load HRIS data
hris_loader = HRISLoader(company_name="My Company", company_domain="mycompany.com")
organization = hris_loader.load_json("hris_data.json")

# Load calendar data
calendar_loader = OutlookCalendarLoader(company_domain="mycompany.com")
events = calendar_loader.load_json("calendar_export.json")

# Generate insights
engine = InsightsEngine(organization)
insights = engine.generate_full_insights(events)

# Generate report
reporter = ReportGenerator()
report = reporter.generate_markdown_report(insights)
print(report)
```

### Additional Analytics
```python
# Individual employee analysis
individual_insights = engine.analyze_individual(events, "john.doe@mycompany.com")

# Manager analysis
from calendar_analytics.analytics import ManagerAnalytics
manager_analytics = ManagerAnalytics(organization)
allocation = manager_analytics.analyze_manager_time(events, "manager@mycompany.com")
at_risk = manager_analytics.identify_at_risk_relationships(events)

# Cross-functional analysis
from calendar_analytics.analytics import CrossFunctionalAnalyzer
cf_analyzer = CrossFunctionalAnalyzer(organization)
health = cf_analyzer.analyze_function_collaboration_health(events)
silos = cf_analyzer.identify_silos(events)
spanners = cf_analyzer.analyze_team_boundary_spanning(events)

# Text analytics
from calendar_analytics.analytics import MeetingTextAnalyzer
text_analyzer = MeetingTextAnalyzer()
keywords = text_analyzer.extract_keywords(events)
naming = text_analyzer.analyze_naming_patterns(events)
```

## Development Workflow
```bash
pytest                  # Run tests
pytest --cov=calendar_analytics
black calendar_analytics/
mypy calendar_analytics/
ruff check calendar_analytics/
```
- Follow cookie-cutter discipline: notebooks and scripts live under structured module paths; keep secrets/data in ignored folders.
- Prefer notebooks for exploratory and final analytical outputs.

## Related References
- Business context: see `docs/business-details.md`.
- Sample outputs and report snippets: see `docs/sample-outputs.md`.
