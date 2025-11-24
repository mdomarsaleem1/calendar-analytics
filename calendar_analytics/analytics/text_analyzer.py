"""Text analytics for meeting subjects and descriptions."""

import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Optional

from ..models.calendar_event import CalendarEvent, MeetingCategory


@dataclass
class TopicCluster:
    """Represents a cluster of related meeting topics."""
    name: str
    keywords: list[str]
    meeting_count: int = 0
    total_hours: float = 0.0
    sample_subjects: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keywords": self.keywords,
            "meeting_count": self.meeting_count,
            "total_hours": round(self.total_hours, 2),
            "sample_subjects": self.sample_subjects[:5],
        }


class MeetingTextAnalyzer:
    """
    Analyzes meeting text (subjects and descriptions) to extract insights.

    Provides:
    - Topic extraction and clustering
    - Meeting category classification
    - Keyword frequency analysis
    - Sentiment indicators
    - Meeting naming patterns
    """

    # Stop words to filter out
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "through", "during",
        "before", "after", "above", "below", "between", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "can", "will", "just", "should", "now", "re", "vs", "w", "meeting",
        "call", "sync", "chat", "discussion", "follow", "quick", "brief",
    }

    # Topic patterns for clustering
    TOPIC_PATTERNS = {
        "product_planning": {
            "keywords": ["roadmap", "product", "feature", "planning", "prd", "spec", "requirements"],
            "pattern": r"(roadmap|product|feature|planning|prd|spec|requirement)",
        },
        "engineering": {
            "keywords": ["technical", "architecture", "code", "review", "design", "api", "system"],
            "pattern": r"(technical|architecture|code|review|design|api|system|engineering)",
        },
        "sprint_agile": {
            "keywords": ["sprint", "standup", "retrospective", "backlog", "scrum", "agile", "kanban"],
            "pattern": r"(sprint|standup|stand-up|retro|backlog|scrum|agile|kanban)",
        },
        "hiring_talent": {
            "keywords": ["interview", "hiring", "candidate", "recruiting", "debrief", "offer"],
            "pattern": r"(interview|hiring|candidate|recruiting|debrief|offer)",
        },
        "customer_client": {
            "keywords": ["customer", "client", "sales", "demo", "pitch", "proposal", "account"],
            "pattern": r"(customer|client|sales|demo|pitch|proposal|account)",
        },
        "project_delivery": {
            "keywords": ["project", "delivery", "milestone", "launch", "release", "deploy"],
            "pattern": r"(project|delivery|milestone|launch|release|deploy|ship)",
        },
        "people_hr": {
            "keywords": ["performance", "career", "growth", "feedback", "development", "review"],
            "pattern": r"(performance|career|growth|feedback|development|1:1|one-on-one)",
        },
        "strategy": {
            "keywords": ["strategy", "vision", "goals", "okr", "kpi", "quarterly", "annual"],
            "pattern": r"(strategy|vision|goals|okr|kpi|quarterly|annual|objectives)",
        },
        "operations": {
            "keywords": ["ops", "operations", "incident", "support", "on-call", "escalation"],
            "pattern": r"(ops|operations|incident|support|on-call|escalation|outage)",
        },
        "training_learning": {
            "keywords": ["training", "workshop", "learning", "onboarding", "tutorial", "bootcamp"],
            "pattern": r"(training|workshop|learning|onboarding|tutorial|bootcamp)",
        },
        "social": {
            "keywords": ["happy hour", "team building", "lunch", "coffee", "celebration", "birthday"],
            "pattern": r"(happy.?hour|team.?building|lunch|coffee|celebration|birthday|social)",
        },
    }

    def __init__(self):
        """Initialize the text analyzer."""
        self.topic_clusters = self._initialize_clusters()

    def _initialize_clusters(self) -> dict[str, TopicCluster]:
        """Initialize topic clusters."""
        return {
            name: TopicCluster(name=name, keywords=config["keywords"])
            for name, config in self.TOPIC_PATTERNS.items()
        }

    def analyze_meeting_topics(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Analyze meeting topics and return comprehensive topic insights.

        Returns:
            Dictionary with topic analysis results
        """
        # Reset clusters
        self.topic_clusters = self._initialize_clusters()

        # Classify each meeting
        classified = []
        unclassified = []

        for event in events:
            text = f"{event.subject} {event.body}".lower()
            matched_topics = []

            for topic_name, config in self.TOPIC_PATTERNS.items():
                if re.search(config["pattern"], text):
                    matched_topics.append(topic_name)
                    cluster = self.topic_clusters[topic_name]
                    cluster.meeting_count += 1
                    cluster.total_hours += event.duration_hours
                    if len(cluster.sample_subjects) < 10:
                        cluster.sample_subjects.append(event.subject)

            if matched_topics:
                classified.append({
                    "subject": event.subject,
                    "topics": matched_topics,
                    "duration": event.duration_minutes,
                })
            else:
                unclassified.append(event.subject)

        # Calculate statistics
        total_events = len(events)
        classification_rate = len(classified) / total_events if total_events > 0 else 0

        # Sort clusters by meeting count
        sorted_clusters = sorted(
            self.topic_clusters.values(),
            key=lambda c: c.meeting_count,
            reverse=True
        )

        return {
            "topic_clusters": [c.to_dict() for c in sorted_clusters if c.meeting_count > 0],
            "classification_rate": round(classification_rate * 100, 1),
            "total_classified": len(classified),
            "total_unclassified": len(unclassified),
            "unclassified_samples": unclassified[:10],
        }

    def extract_keywords(
        self,
        events: list[CalendarEvent],
        top_n: int = 50
    ) -> dict:
        """
        Extract most common keywords from meeting subjects.

        Args:
            events: List of calendar events
            top_n: Number of top keywords to return

        Returns:
            Dictionary with keyword frequency data
        """
        word_counts: Counter = Counter()

        for event in events:
            # Clean and tokenize subject
            text = event.subject.lower()
            text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
            words = text.split()

            # Filter and count
            for word in words:
                if len(word) > 2 and word not in self.STOP_WORDS:
                    word_counts[word] += 1

        # Get top keywords
        top_keywords = word_counts.most_common(top_n)

        # Calculate word clouds by category
        category_words: dict[str, Counter] = defaultdict(Counter)

        for event in events:
            category = event.classify_meeting_category()
            text = event.subject.lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            words = text.split()

            for word in words:
                if len(word) > 2 and word not in self.STOP_WORDS:
                    category_words[category.value][word] += 1

        return {
            "top_keywords": [
                {"word": word, "count": count}
                for word, count in top_keywords
            ],
            "total_unique_words": len(word_counts),
            "by_category": {
                cat: [
                    {"word": w, "count": c}
                    for w, c in counter.most_common(10)
                ]
                for cat, counter in category_words.items()
            },
        }

    def analyze_meeting_categories(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Categorize meetings and analyze distribution.

        Returns:
            Category breakdown with statistics
        """
        category_stats: dict[MeetingCategory, dict] = defaultdict(
            lambda: {"count": 0, "hours": 0, "subjects": []}
        )

        for event in events:
            category = event.classify_meeting_category()
            category_stats[category]["count"] += 1
            category_stats[category]["hours"] += event.duration_hours

            if len(category_stats[category]["subjects"]) < 5:
                category_stats[category]["subjects"].append(event.subject)

        # Convert to output format
        results = {}
        total_events = len(events)
        total_hours = sum(e.duration_hours for e in events)

        for category, stats in category_stats.items():
            results[category.value] = {
                "count": stats["count"],
                "hours": round(stats["hours"], 2),
                "percentage_of_meetings": round(
                    stats["count"] / total_events * 100, 1
                ) if total_events else 0,
                "percentage_of_time": round(
                    stats["hours"] / total_hours * 100, 1
                ) if total_hours else 0,
                "sample_subjects": stats["subjects"],
            }

        # Sort by count
        sorted_results = dict(
            sorted(results.items(), key=lambda x: x[1]["count"], reverse=True)
        )

        return {
            "categories": sorted_results,
            "total_meetings": total_events,
            "total_hours": round(total_hours, 2),
            "most_common_category": max(
                results.keys(),
                key=lambda k: results[k]["count"]
            ) if results else None,
        }

    def analyze_naming_patterns(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Analyze meeting naming patterns and conventions.

        Identifies:
        - Common prefixes/suffixes
        - Naming conventions used
        - Quality of meeting names
        """
        # Analyze patterns
        patterns = {
            "has_date": 0,
            "has_attendee_names": 0,
            "uses_abbreviations": 0,
            "is_vague": 0,  # Generic names like "Meeting" or "Call"
            "is_descriptive": 0,  # Specific, action-oriented names
            "has_project_code": 0,
            "has_recurrence_indicator": 0,
        }

        vague_subjects = []
        well_named = []

        for event in events:
            subject = event.subject.lower()

            # Check for date patterns
            if re.search(r'\d{1,2}/\d{1,2}|\d{4}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec', subject):
                patterns["has_date"] += 1

            # Check for attendee names (common name patterns)
            if re.search(r'with\s+\w+|\/\s*\w+|<>|&', subject):
                patterns["has_attendee_names"] += 1

            # Check for abbreviations (all caps words)
            if re.search(r'\b[A-Z]{2,}\b', event.subject):
                patterns["uses_abbreviations"] += 1

            # Check for vague names
            if re.match(r'^(meeting|call|sync|chat|catch up|check in|touchbase|touch base)$', subject.strip()):
                patterns["is_vague"] += 1
                vague_subjects.append(event.subject)

            # Check for descriptive names (contains action words)
            action_words = ["review", "discuss", "plan", "decide", "present", "analyze", "define", "create", "design"]
            if any(word in subject for word in action_words):
                patterns["is_descriptive"] += 1
                if len(well_named) < 10:
                    well_named.append(event.subject)

            # Check for project codes (alphanumeric patterns)
            if re.search(r'\b[A-Z]+-\d+\b|\b[A-Z]{2,4}-\w+\b', event.subject):
                patterns["has_project_code"] += 1

            # Check for recurrence indicators
            if re.search(r'weekly|daily|monthly|bi-weekly|biweekly|recurring', subject):
                patterns["has_recurrence_indicator"] += 1

        total = len(events)

        # Calculate naming quality score (0-100)
        quality_score = 0
        if total > 0:
            # Reward descriptive names
            quality_score += (patterns["is_descriptive"] / total) * 40
            # Penalize vague names
            quality_score -= (patterns["is_vague"] / total) * 30
            # Slight bonus for project codes (organized)
            quality_score += (patterns["has_project_code"] / total) * 20
            # Slight penalty for just dates (not descriptive)
            quality_score -= (patterns["has_date"] / total) * 10

            quality_score = max(0, min(100, quality_score + 50))  # Normalize to 0-100

        return {
            "pattern_counts": {k: v for k, v in patterns.items()},
            "pattern_percentages": {
                k: round(v / total * 100, 1) if total else 0
                for k, v in patterns.items()
            },
            "naming_quality_score": round(quality_score, 1),
            "vague_meeting_count": patterns["is_vague"],
            "vague_meeting_samples": vague_subjects[:10],
            "well_named_samples": well_named,
            "recommendations": self._get_naming_recommendations(patterns, total),
        }

    def _get_naming_recommendations(self, patterns: dict, total: int) -> list[str]:
        """Generate recommendations for improving meeting naming."""
        recommendations = []

        if total == 0:
            return recommendations

        vague_pct = patterns["is_vague"] / total * 100

        if vague_pct > 20:
            recommendations.append(
                f"{vague_pct:.0f}% of meetings have vague names. Use descriptive names "
                "that indicate the purpose (e.g., 'Review Q4 Marketing Plan' instead of 'Meeting')."
            )

        if patterns["is_descriptive"] / total < 0.3:
            recommendations.append(
                "Include action verbs in meeting names to clarify purpose "
                "(e.g., 'Decide on vendor selection' or 'Review design mockups')."
            )

        if patterns["has_project_code"] / total < 0.1:
            recommendations.append(
                "Consider using project codes or tags to help with filtering and reporting "
                "(e.g., '[PROJ-123] Sprint Planning')."
            )

        return recommendations

    def detect_meeting_sentiment(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Detect sentiment indicators in meeting subjects.

        Identifies potentially concerning or positive meeting patterns.
        """
        # Sentiment indicators
        urgent_patterns = [
            r'\burgent\b', r'\basap\b', r'\bemergency\b', r'\bcritical\b',
            r'\bimmediate\b', r'\bescalation\b', r'\bsev\s*[1-2]\b',
        ]

        positive_patterns = [
            r'\bcelebrat', r'\bcongrat', r'\bsuccess\b', r'\bwin\b',
            r'\bachiev', r'\blaunch\b', r'\bship', r'\bwelcome\b',
        ]

        potentially_negative = [
            r'\bissue\b', r'\bproblem\b', r'\bfailed\b', r'\bblocked\b',
            r'\bincident\b', r'\boutage\b', r'\bescalat', r'\bbug\b',
        ]

        results = {
            "urgent": [],
            "positive": [],
            "potentially_negative": [],
            "neutral": [],
        }

        for event in events:
            subject_lower = event.subject.lower()
            categorized = False

            for pattern in urgent_patterns:
                if re.search(pattern, subject_lower):
                    results["urgent"].append({
                        "subject": event.subject,
                        "date": event.start_time.isoformat(),
                    })
                    categorized = True
                    break

            if not categorized:
                for pattern in positive_patterns:
                    if re.search(pattern, subject_lower):
                        results["positive"].append({
                            "subject": event.subject,
                            "date": event.start_time.isoformat(),
                        })
                        categorized = True
                        break

            if not categorized:
                for pattern in potentially_negative:
                    if re.search(pattern, subject_lower):
                        results["potentially_negative"].append({
                            "subject": event.subject,
                            "date": event.start_time.isoformat(),
                        })
                        categorized = True
                        break

            if not categorized:
                results["neutral"].append(event.subject)

        return {
            "summary": {
                "urgent_count": len(results["urgent"]),
                "positive_count": len(results["positive"]),
                "potentially_negative_count": len(results["potentially_negative"]),
                "neutral_count": len(results["neutral"]),
            },
            "urgent_meetings": results["urgent"][:10],
            "positive_meetings": results["positive"][:10],
            "potentially_negative_meetings": results["potentially_negative"][:10],
        }

    def get_comprehensive_text_analysis(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Run all text analyses and return comprehensive results.
        """
        return {
            "topic_analysis": self.analyze_meeting_topics(events),
            "keyword_analysis": self.extract_keywords(events),
            "category_analysis": self.analyze_meeting_categories(events),
            "naming_patterns": self.analyze_naming_patterns(events),
            "sentiment_analysis": self.detect_meeting_sentiment(events),
        }
