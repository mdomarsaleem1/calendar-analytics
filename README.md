# Calendar Analytics

A comprehensive analytics platform for analyzing Outlook 365 calendar data combined with HRIS organizational data to generate actionable meeting insights.

## Features

### Core Analytics

- **Meeting Size & Duration Matrix (3x3)**: Understand how time is distributed across small/medium/large meetings and short/medium/long durations
- **Recurring vs Ad-hoc Analysis**: Track the balance between scheduled recurring meetings and ad-hoc meetings, broken down by employee level
- **1:1 vs Team Meetings**: Analyze the distribution of one-on-one meetings vs small team, large team, and all-hands meetings
- **Manager Time Analysis**: Track manager time in 1:1s, skip-levels, team meetings, and identify potential micromanagement patterns
- **Cross-Functional Interactions**: Visualize collaboration patterns between different job functions, identify silos, and find boundary spanners
- **Text Analytics**: Extract meeting topics, categorize meetings, analyze naming patterns, and detect sentiment indicators
- **Internal vs External Meetings**: Track customer-facing time, especially relevant for Sales and Customer Success teams
- **Performance Best Practices**: Generate actionable recommendations based on meeting behavior patterns

### Additional Insights

- **Calendar Fragmentation**: Measure how scattered meetings are throughout the day, affecting focus time
- **Meeting Efficiency Metrics**: Response rates, acceptance rates, standard duration usage
- **Meeting Cost Estimation**: Calculate estimated meeting costs based on attendee hours
- **Time Pattern Analysis**: Identify busiest days/hours, early morning/late evening meetings
- **Back-to-Back Meeting Detection**: Find scheduling conflicts and buffer time issues
- **At-Risk Relationships**: Identify manager-report pairs that may need more 1:1 time
- **Boundary Spanners**: Identify employees who connect different functions

## Installation

```bash
# Clone the repository
git clone https://github.com/example/calendar-analytics.git
cd calendar-analytics

# Install the package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Run Demo

See the analytics in action with generated sample data:

```bash
calendar-analytics demo
```

### Generate Sample Data

Create sample organization and calendar data for testing:

```bash
calendar-analytics generate-sample --employees 50 --days 30 --output ./sample_data
```

### Analyze Real Data

Run analysis on your organization's data:

```bash
calendar-analytics analyze \
    --hris ./hris_data.json \
    --calendars ./calendar_exports/ \
    --output ./report.md \
    --format markdown
```

## Data Input Formats

### HRIS Data (JSON)

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

### HRIS Data (CSV)

```csv
employee_id,email,name,job_title,level,function,team,manager_email,location
EMP001,john.doe@example.com,John Doe,Software Engineer,Senior IC,Engineering,Platform,jane.smith@example.com,San Francisco
```

### Calendar Data (Outlook Export JSON)

Compatible with Microsoft Graph API calendar export format:

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

## Python API

### Basic Usage

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

### Individual Analysis

```python
# Analyze a specific employee's calendar
individual_insights = engine.analyze_individual(events, "john.doe@mycompany.com")
```

### Manager-Specific Analytics

```python
from calendar_analytics.analytics import ManagerAnalytics

manager_analytics = ManagerAnalytics(organization)

# Analyze a specific manager's time allocation
allocation = manager_analytics.analyze_manager_time(events, "manager@mycompany.com")
print(f"1:1 time: {allocation.one_on_one_hours} hours")
print(f"Monitoring score: {allocation.monitoring_indicator}/10")

# Identify at-risk manager-report relationships
at_risk = manager_analytics.identify_at_risk_relationships(events)
```

### Cross-Functional Analysis

```python
from calendar_analytics.analytics import CrossFunctionalAnalyzer

cf_analyzer = CrossFunctionalAnalyzer(organization)

# Get collaboration health score
health = cf_analyzer.analyze_function_collaboration_health(events)
print(f"Health Score: {health['health_score']}/100")

# Identify organizational silos
silos = cf_analyzer.identify_silos(events)

# Find boundary spanners
spanners = cf_analyzer.analyze_team_boundary_spanning(events)
```

### Text Analytics

```python
from calendar_analytics.analytics import MeetingTextAnalyzer

text_analyzer = MeetingTextAnalyzer()

# Analyze meeting topics
topics = text_analyzer.analyze_meeting_topics(events)

# Extract keywords
keywords = text_analyzer.extract_keywords(events)

# Analyze meeting naming patterns
naming = text_analyzer.analyze_naming_patterns(events)
```

## Output Insights

### Size-Duration Matrix

```
| Size \ Duration | Short (≤30m) | Medium (31-60m) | Long (>60m) |
|-----------------|--------------|-----------------|-------------|
| Small (1-2)     | 45 (22.5h)   | 30 (30h)        | 5 (7.5h)    |
| Medium (3-5)    | 20 (10h)     | 35 (35h)        | 15 (22.5h)  |
| Large (6+)      | 5 (2.5h)     | 10 (10h)        | 8 (12h)     |
```

### Best Practices Recommendations

The system generates actionable recommendations:

**High Priority:**
- Excessive meeting time (>6 hrs/day)
- High calendar fragmentation
- Meetings defaulting to 1 hour

**Medium Priority:**
- High recurring meeting percentage (>70%)
- Low response rates
- Vague meeting names

**Positive Patterns Detected:**
- Healthy 1:1 ratio
- Good cross-functional collaboration
- Consistent meeting lengths

## Architecture

```
calendar_analytics/
├── models/
│   ├── calendar_event.py    # Calendar event data model
│   └── employee.py          # Employee and organization models
├── data_loaders/
│   ├── outlook_loader.py    # Outlook 365 data loader
│   ├── hris_loader.py       # HRIS data loader
│   └── data_processor.py    # Data enrichment and processing
├── analytics/
│   ├── meeting_analyzer.py  # Core meeting analytics
│   ├── manager_analytics.py # Manager-specific analytics
│   ├── cross_functional.py  # Cross-functional analysis
│   ├── text_analyzer.py     # Text/NLP analytics
│   └── insights_engine.py   # Main insights orchestrator
├── utils/
│   ├── sample_data_generator.py  # Sample data generation
│   └── report_generator.py       # Report generation
├── cli.py                   # Command-line interface
└── __init__.py
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=calendar_analytics

# Format code
black calendar_analytics/

# Type checking
mypy calendar_analytics/

# Linting
ruff check calendar_analytics/
```

## License

MIT License - see LICENSE file for details.
