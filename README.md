# Calendar Analytics

A lightweight overview of the Outlook 365 + HRIS analytics toolkit that surfaces meeting hygiene, collaboration health, and cost insights.

## Overview
- Connect Outlook calendar exports with HRIS metadata to understand how teams meet and collaborate.
- Notebook-friendly workflows for exploration; CLI for repeatable jobs.
- Cookie-cutter layout with sensitive data kept out of version control via `.gitignore`.

## Key Features
- Meeting intelligence: size/duration matrix, recurring vs ad-hoc mix, 1:1 vs team vs all-hands distribution.
- Collaboration health: cross-functional interactions, boundary spanners, and silo detection.
- Manager analytics: 1:1 cadence, skip-level visibility, and potential micromanagement signals.
- Calendar hygiene: fragmentation, back-to-back detection, default duration adoption, and response/acceptance trends.
- Cost and value: estimated meeting costs plus internal vs external time mix.

## High-Level Architecture
- **Ingest**: Outlook and HRIS loaders enrich events with organizational context.
- **Analyze**: Modular analytics engine (meeting, manager, cross-functional, text) orchestrated by `InsightsEngine`.
- **Deliver**: Reports and notebooks via CLI (`calendar-analytics`) and Python API; sample data generator for demos.

## Documentation
Detailed specs, business context, and sample outputs have moved to the `docs/` folder:
- Technical spec and usage: `docs/tech-spec.md`
- Business context and roadmap: `docs/business-details.md`
- Sample outputs and recommendations: `docs/sample-outputs.md`
