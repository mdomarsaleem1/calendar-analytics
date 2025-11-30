"""Command-line interface for calendar analytics."""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calendar Analytics - Analyze Outlook 365 calendar data with HRIS integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate sample data for testing
  calendar-analytics generate-sample --employees 50 --days 30 --output ./sample_data

  # Run analysis on real data
  calendar-analytics analyze --hris ./hris_data.json --calendars ./calendars/ --output ./report.md

  # Generate individual report
  calendar-analytics individual --email john.doe@example.com --output ./john_report.md

  # Run demo with sample data
  calendar-analytics demo
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate sample data command
    gen_parser = subparsers.add_parser("generate-sample", help="Generate sample data for testing")
    gen_parser.add_argument("--employees", type=int, default=50, help="Number of employees (default: 50)")
    gen_parser.add_argument("--days", type=int, default=30, help="Number of days of data (default: 30)")
    gen_parser.add_argument("--output", "-o", type=str, default="./sample_data", help="Output directory")
    gen_parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    gen_parser.add_argument("--domain", type=str, default="example.com", help="Company email domain")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run full calendar analysis")
    analyze_parser.add_argument("--hris", "-h", type=str, required=True, help="Path to HRIS data file (JSON/CSV)")
    analyze_parser.add_argument("--calendars", "-c", type=str, required=True, help="Path to calendars directory or file")
    analyze_parser.add_argument("--output", "-o", type=str, default="./report.md", help="Output report path")
    analyze_parser.add_argument("--format", type=str, choices=["markdown", "html", "json", "text"], default="markdown")
    analyze_parser.add_argument("--domain", type=str, help="Company email domain (auto-detected if not provided)")

    # Individual analysis command
    ind_parser = subparsers.add_parser("individual", help="Generate individual report")
    ind_parser.add_argument("--email", "-e", type=str, required=True, help="Employee email to analyze")
    ind_parser.add_argument("--hris", type=str, required=True, help="Path to HRIS data file")
    ind_parser.add_argument("--calendars", type=str, required=True, help="Path to calendars directory")
    ind_parser.add_argument("--output", "-o", type=str, help="Output report path")
    ind_parser.add_argument("--format", type=str, choices=["markdown", "html", "json"], default="markdown")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo with generated sample data")
    demo_parser.add_argument("--employees", type=int, default=30, help="Number of employees")
    demo_parser.add_argument("--days", type=int, default=14, help="Number of days")

    args = parser.parse_args()

    if args.command == "generate-sample":
        run_generate_sample(args)
    elif args.command == "analyze":
        run_analyze(args)
    elif args.command == "individual":
        run_individual(args)
    elif args.command == "demo":
        run_demo(args)
    else:
        parser.print_help()
        sys.exit(1)


def run_generate_sample(args):
    """Generate sample data."""
    from .utils.sample_data_generator import SampleDataGenerator

    print(f"Generating sample data...")
    print(f"  Employees: {args.employees}")
    print(f"  Days: {args.days}")
    print(f"  Domain: {args.domain}")

    generator = SampleDataGenerator(
        company_domain=args.domain,
        seed=args.seed
    )

    # Generate organization
    org = generator.generate_organization(
        employee_count=args.employees,
        company_name="Sample Corp"
    )
    print(f"  Generated {len(org.employees)} employees")

    # Generate calendar events
    calendars = generator.generate_calendar_events(
        organization=org,
        days=args.days
    )

    total_events = sum(len(events) for events in calendars.values())
    print(f"  Generated {total_events} calendar events")

    # Export data
    generator.export_sample_data(org, calendars, args.output)

    print(f"\nSample data saved to: {args.output}")


def run_analyze(args):
    """Run full calendar analysis."""
    from .data_loaders.hris_loader import HRISLoader
    from .data_loaders.outlook_loader import OutlookCalendarLoader
    from .analytics.insights_engine import InsightsEngine
    from .utils.report_generator import ReportGenerator

    print("Loading data...")

    # Load HRIS data
    hris_path = Path(args.hris)
    hris_loader = HRISLoader()

    if hris_path.suffix == ".json":
        org = hris_loader.load_json(hris_path)
    else:
        org = hris_loader.load_csv(hris_path)

    print(f"  Loaded {len(org.employees)} employees from HRIS")

    # Determine domain
    domain = args.domain or org.domain
    if not domain and org.employees:
        first_email = list(org.employees.keys())[0]
        domain = first_email.split("@")[1] if "@" in first_email else ""

    # Load calendar data
    calendar_loader = OutlookCalendarLoader(company_domain=domain)
    calendars_path = Path(args.calendars)

    all_events = []

    if calendars_path.is_dir():
        # Load all calendar files in directory
        for cal_file in calendars_path.glob("*.json"):
            email = cal_file.stem.replace("_at_", "@").replace("_", ".")
            events = calendar_loader.load_json(cal_file, email)
            all_events.extend(events)

        for cal_file in calendars_path.glob("*.csv"):
            email = cal_file.stem.replace("_at_", "@").replace("_", ".")
            events = calendar_loader.load_csv(cal_file, email)
            all_events.extend(events)
    else:
        # Single file
        if calendars_path.suffix == ".json":
            all_events = calendar_loader.load_json(calendars_path)
        else:
            all_events = calendar_loader.load_csv(calendars_path)

    print(f"  Loaded {len(all_events)} calendar events")

    # Deduplicate events (same event may appear in multiple calendars)
    unique_events = {}
    for event in all_events:
        key = f"{event.subject}_{event.start_time}_{event.organizer_email}"
        if key not in unique_events:
            unique_events[key] = event

    events = list(unique_events.values())
    print(f"  {len(events)} unique events after deduplication")

    # Run analysis
    print("\nRunning analysis...")
    engine = InsightsEngine(org)
    insights = engine.generate_full_insights(events)

    # Generate report
    print("\nGenerating report...")
    reporter = ReportGenerator()
    reporter.save_report(insights, args.output, args.format)

    # Print summary
    summary = insights.get("summary", {})
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    print(f"Total Meetings: {summary.get('total_meetings', 'N/A')}")
    print(f"Total Hours: {summary.get('total_hours', 'N/A'):.1f}")
    print(f"Avg per Day: {summary.get('avg_meetings_per_day', 'N/A'):.1f} meetings, {summary.get('avg_hours_per_day', 'N/A'):.1f} hours")
    print(f"\nReport saved to: {args.output}")


def run_individual(args):
    """Run individual analysis."""
    from .data_loaders.hris_loader import HRISLoader
    from .data_loaders.outlook_loader import OutlookCalendarLoader
    from .analytics.insights_engine import InsightsEngine
    from .utils.report_generator import ReportGenerator

    print(f"Analyzing calendar for: {args.email}")

    # Load data (similar to analyze command)
    hris_path = Path(args.hris)
    hris_loader = HRISLoader()

    if hris_path.suffix == ".json":
        org = hris_loader.load_json(hris_path)
    else:
        org = hris_loader.load_csv(hris_path)

    domain = org.domain or args.email.split("@")[1]
    calendar_loader = OutlookCalendarLoader(company_domain=domain)

    calendars_path = Path(args.calendars)
    all_events = []

    if calendars_path.is_dir():
        for cal_file in calendars_path.glob("*.json"):
            events = calendar_loader.load_json(cal_file)
            all_events.extend(events)
    else:
        all_events = calendar_loader.load_json(calendars_path)

    # Run individual analysis
    engine = InsightsEngine(org)
    insights = engine.analyze_individual(all_events, args.email)

    # Save report
    output_path = args.output or f"./report_{args.email.replace('@', '_')}.{args.format}"

    with open(output_path, "w") as f:
        if args.format == "json":
            json.dump(insights, f, indent=2, default=str)
        else:
            f.write(json.dumps(insights, indent=2, default=str))

    print(f"Individual report saved to: {output_path}")


def run_demo(args):
    """Run demo with sample data."""
    from .utils.sample_data_generator import SampleDataGenerator
    from .analytics.insights_engine import InsightsEngine
    from .utils.report_generator import ReportGenerator

    print("=" * 60)
    print("CALENDAR ANALYTICS DEMO")
    print("=" * 60)

    print(f"\nGenerating sample organization ({args.employees} employees)...")
    generator = SampleDataGenerator(company_domain="demo.com", seed=42)

    org = generator.generate_organization(employee_count=args.employees)
    print(f"  ✓ Created {len(org.employees)} employees")
    print(f"  ✓ {len(org.get_all_managers())} managers")

    print(f"\nGenerating {args.days} days of calendar data...")
    calendars = generator.generate_calendar_events(org, days=args.days)

    # Collect all events
    all_events = []
    for events in calendars.values():
        all_events.extend(events)

    # Deduplicate
    unique_events = {}
    for event in all_events:
        key = f"{event.event_id}"
        if key not in unique_events:
            unique_events[key] = event

    events = list(unique_events.values())
    print(f"  ✓ Generated {len(events)} unique meetings")

    print("\nRunning analysis...")
    engine = InsightsEngine(org)
    insights = engine.generate_full_insights(events)

    # Print results
    reporter = ReportGenerator()
    print("\n" + reporter.generate_executive_summary(insights))

    # Print key insights
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)

    # Size-Duration Matrix
    matrix = insights.get("size_duration_matrix", {}).get("matrix", {})
    if matrix:
        print("\n📊 Meeting Size/Duration Distribution:")
        print("   Small meetings (1-2 people): ", end="")
        small = matrix.get("small", {})
        print(f"{small.get('short', {}).get('count', 0) + small.get('medium', {}).get('count', 0) + small.get('long', {}).get('count', 0)} meetings")

        print("   Large meetings (6+ people): ", end="")
        large = matrix.get("large", {})
        print(f"{large.get('short', {}).get('count', 0) + large.get('medium', {}).get('count', 0) + large.get('long', {}).get('count', 0)} meetings")

    # Cross-functional health
    cf = insights.get("cross_functional_health", {})
    if cf:
        print(f"\n🤝 Cross-Functional Collaboration:")
        print(f"   Health Score: {cf.get('health_score', 0):.0f}/100 ({cf.get('health_rating', 'N/A')})")
        print(f"   Cross-functional meetings: {cf.get('cross_functional_percentage', 0):.1f}%")

    # Best practices
    bp = insights.get("best_practices", {})
    if bp.get("high_priority"):
        print(f"\n⚠️  High Priority Issues: {len(bp['high_priority'])}")
        for issue in bp["high_priority"][:2]:
            print(f"   • {issue['issue']}")

    if bp.get("positive_patterns"):
        print(f"\n✅ Positive Patterns: {len(bp['positive_patterns'])}")
        for pattern in bp["positive_patterns"][:2]:
            print(f"   • {pattern['pattern']}")

    print("\n" + "=" * 60)
    print("Demo complete! Use 'calendar-analytics analyze' with your own data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
