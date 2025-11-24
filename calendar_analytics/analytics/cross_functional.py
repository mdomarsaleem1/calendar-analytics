"""Cross-functional interaction analytics."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from ..models.calendar_event import CalendarEvent
from ..models.employee import Organization, Employee, JobFunction


@dataclass
class FunctionInteraction:
    """Represents interactions between two functions."""
    function_a: JobFunction
    function_b: JobFunction
    meeting_count: int = 0
    total_hours: float = 0.0
    unique_participants: set = field(default_factory=set)
    meeting_subjects: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "function_a": self.function_a.value,
            "function_b": self.function_b.value,
            "meeting_count": self.meeting_count,
            "total_hours": round(self.total_hours, 2),
            "unique_participants": len(self.unique_participants),
            "sample_subjects": self.meeting_subjects[:5],
        }


class CrossFunctionalAnalyzer:
    """
    Analyzes interactions between different job functions and teams.

    Helps identify:
    - Collaboration patterns between functions
    - Siloed teams
    - Cross-functional communication health
    - Team boundary spanning
    """

    def __init__(self, organization: Organization):
        """
        Initialize with organization data.

        Args:
            organization: Organization with employee data
        """
        self.org = organization

    def analyze_function_interactions(
        self,
        events: list[CalendarEvent]
    ) -> dict[str, FunctionInteraction]:
        """
        Analyze meeting interactions between different job functions.

        Returns:
            Dictionary mapping function pair key to interaction data
        """
        interactions: dict[str, FunctionInteraction] = {}

        for event in events:
            # Get all attendees with their functions
            attendees = event.get_attendee_emails()
            functions_in_meeting: dict[JobFunction, set] = defaultdict(set)

            for email in attendees:
                employee = self.org.get_employee(email)
                if employee:
                    functions_in_meeting[employee.job_function].add(email)

            # Skip if only one function represented
            if len(functions_in_meeting) < 2:
                continue

            # Record interactions between all function pairs
            function_list = list(functions_in_meeting.keys())

            for i in range(len(function_list)):
                for j in range(i + 1, len(function_list)):
                    func_a = function_list[i]
                    func_b = function_list[j]

                    # Create consistent key (alphabetically sorted)
                    key = tuple(sorted([func_a.value, func_b.value]))
                    key_str = f"{key[0]}:{key[1]}"

                    if key_str not in interactions:
                        interactions[key_str] = FunctionInteraction(
                            function_a=func_a if func_a.value == key[0] else func_b,
                            function_b=func_b if func_b.value == key[1] else func_a,
                        )

                    interaction = interactions[key_str]
                    interaction.meeting_count += 1
                    interaction.total_hours += event.duration_hours
                    interaction.unique_participants.update(functions_in_meeting[func_a])
                    interaction.unique_participants.update(functions_in_meeting[func_b])

                    if len(interaction.meeting_subjects) < 10:
                        interaction.meeting_subjects.append(event.subject)

        return interactions

    def get_interaction_matrix(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Create a matrix showing interaction frequency between all functions.

        Returns:
            Dictionary with matrix data and statistics
        """
        interactions = self.analyze_function_interactions(events)

        # Build matrix
        functions = list(JobFunction)
        matrix: dict[str, dict[str, dict]] = {}

        for func in functions:
            matrix[func.value] = {}
            for other_func in functions:
                if func == other_func:
                    matrix[func.value][other_func.value] = {"count": 0, "hours": 0, "self": True}
                else:
                    # Find interaction data
                    key = tuple(sorted([func.value, other_func.value]))
                    key_str = f"{key[0]}:{key[1]}"

                    if key_str in interactions:
                        interaction = interactions[key_str]
                        matrix[func.value][other_func.value] = {
                            "count": interaction.meeting_count,
                            "hours": round(interaction.total_hours, 2),
                            "self": False,
                        }
                    else:
                        matrix[func.value][other_func.value] = {"count": 0, "hours": 0, "self": False}

        # Calculate statistics
        total_cross_functional = sum(i.meeting_count for i in interactions.values())
        total_cross_functional_hours = sum(i.total_hours for i in interactions.values())

        # Find strongest and weakest connections
        sorted_interactions = sorted(
            interactions.values(),
            key=lambda x: x.meeting_count,
            reverse=True
        )

        strongest = [i.to_dict() for i in sorted_interactions[:5]]
        weakest = [i.to_dict() for i in sorted_interactions[-5:] if i.meeting_count > 0]

        return {
            "matrix": matrix,
            "total_cross_functional_meetings": total_cross_functional,
            "total_cross_functional_hours": round(total_cross_functional_hours, 2),
            "strongest_connections": strongest,
            "weakest_connections": weakest,
            "function_count": len([f for f in functions if any(
                matrix[f.value][other.value]["count"] > 0
                for other in functions if f != other
            )]),
        }

    def identify_silos(
        self,
        events: list[CalendarEvent],
        threshold_pct: float = 80.0
    ) -> list[dict]:
        """
        Identify functions or teams that may be siloed.

        A function is considered siloed if more than threshold_pct of their
        meetings are with the same function.
        """
        # Calculate meetings per function
        function_meetings: dict[JobFunction, dict] = defaultdict(
            lambda: {"total": 0, "same_function": 0, "cross_function": 0}
        )

        for event in events:
            attendees = event.get_attendee_emails()
            functions_in_meeting: set[JobFunction] = set()

            for email in attendees:
                employee = self.org.get_employee(email)
                if employee:
                    functions_in_meeting.add(employee.job_function)

            # Count for each function
            for func in functions_in_meeting:
                function_meetings[func]["total"] += 1
                if len(functions_in_meeting) == 1:
                    function_meetings[func]["same_function"] += 1
                else:
                    function_meetings[func]["cross_function"] += 1

        # Identify silos
        silos = []
        for func, counts in function_meetings.items():
            if counts["total"] == 0:
                continue

            same_function_pct = counts["same_function"] / counts["total"] * 100

            if same_function_pct >= threshold_pct:
                silos.append({
                    "function": func.value,
                    "total_meetings": counts["total"],
                    "same_function_meetings": counts["same_function"],
                    "cross_function_meetings": counts["cross_function"],
                    "same_function_percentage": round(same_function_pct, 1),
                    "silo_severity": "high" if same_function_pct >= 90 else "medium",
                    "recommendations": [
                        f"Schedule regular cross-functional syncs with related teams",
                        f"Include {func.value} in broader planning meetings",
                        f"Create joint projects with other functions",
                    ],
                })

        # Sort by severity
        silos.sort(key=lambda x: x["same_function_percentage"], reverse=True)

        return silos

    def analyze_team_boundary_spanning(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Identify individuals who frequently connect different functions.

        These "boundary spanners" are valuable for cross-functional communication.
        """
        # Track cross-functional meeting participation
        boundary_spanners: dict[str, dict] = defaultdict(
            lambda: {
                "cross_functional_meetings": 0,
                "functions_connected": set(),
                "total_meetings": 0,
            }
        )

        for event in events:
            attendees = event.get_attendee_emails()

            # Identify functions in meeting
            functions_in_meeting: set[JobFunction] = set()
            for email in attendees:
                employee = self.org.get_employee(email)
                if employee:
                    functions_in_meeting.add(employee.job_function)

            is_cross_functional = len(functions_in_meeting) > 1

            # Update each attendee's stats
            for email in attendees:
                employee = self.org.get_employee(email)
                if not employee:
                    continue

                boundary_spanners[email]["total_meetings"] += 1
                boundary_spanners[email]["name"] = employee.name
                boundary_spanners[email]["function"] = employee.job_function.value

                if is_cross_functional:
                    boundary_spanners[email]["cross_functional_meetings"] += 1
                    boundary_spanners[email]["functions_connected"].update(
                        f.value for f in functions_in_meeting
                    )

        # Calculate scores and rank
        results = []
        for email, data in boundary_spanners.items():
            if data["total_meetings"] == 0:
                continue

            cross_functional_ratio = data["cross_functional_meetings"] / data["total_meetings"]
            functions_connected = len(data["functions_connected"])

            # Boundary spanning score (0-10)
            score = (cross_functional_ratio * 5) + min(functions_connected, 5)

            results.append({
                "email": email,
                "name": data["name"],
                "function": data["function"],
                "total_meetings": data["total_meetings"],
                "cross_functional_meetings": data["cross_functional_meetings"],
                "cross_functional_ratio": round(cross_functional_ratio * 100, 1),
                "functions_connected": list(data["functions_connected"]),
                "boundary_spanning_score": round(score, 1),
            })

        # Sort by score
        results.sort(key=lambda x: x["boundary_spanning_score"], reverse=True)

        return {
            "boundary_spanners": results[:20],  # Top 20
            "avg_cross_functional_ratio": round(
                sum(r["cross_functional_ratio"] for r in results) / len(results), 1
            ) if results else 0,
            "employees_analyzed": len(results),
        }

    def analyze_function_collaboration_health(
        self,
        events: list[CalendarEvent]
    ) -> dict:
        """
        Provide an overall assessment of cross-functional collaboration health.
        """
        matrix = self.get_interaction_matrix(events)
        silos = self.identify_silos(events)
        boundary_analysis = self.analyze_team_boundary_spanning(events)

        # Calculate health metrics
        total_meetings = len(events)
        cross_functional_meetings = matrix["total_cross_functional_meetings"]
        cross_functional_ratio = cross_functional_meetings / total_meetings if total_meetings > 0 else 0

        # Expected connections (for active functions)
        active_functions = matrix["function_count"]
        expected_connections = (active_functions * (active_functions - 1)) / 2
        actual_connections = len([
            c for c in matrix["strongest_connections"]
            if c["meeting_count"] > 0
        ]) + len([
            c for c in matrix["weakest_connections"]
            if c["meeting_count"] > 0
        ])

        # Health score (0-100)
        health_score = 0

        # Factor 1: Cross-functional meeting ratio (0-30 points)
        health_score += min(cross_functional_ratio * 100, 30)

        # Factor 2: Low silo count (0-30 points)
        silo_penalty = len(silos) * 10
        health_score += max(30 - silo_penalty, 0)

        # Factor 3: Boundary spanner presence (0-20 points)
        if boundary_analysis["boundary_spanners"]:
            top_spanners = boundary_analysis["boundary_spanners"][:10]
            avg_score = sum(s["boundary_spanning_score"] for s in top_spanners) / len(top_spanners)
            health_score += avg_score * 2

        # Factor 4: Connection coverage (0-20 points)
        if expected_connections > 0:
            coverage = actual_connections / expected_connections
            health_score += coverage * 20

        health_score = min(round(health_score, 1), 100)

        # Generate recommendations
        recommendations = []

        if cross_functional_ratio < 0.3:
            recommendations.append(
                "Cross-functional meeting ratio is low. Consider creating more "
                "joint initiatives and shared goals between teams."
            )

        if silos:
            silo_names = [s["function"] for s in silos[:3]]
            recommendations.append(
                f"Potential silos identified in: {', '.join(silo_names)}. "
                "Focus on improving collaboration with these teams."
            )

        if boundary_analysis["avg_cross_functional_ratio"] < 30:
            recommendations.append(
                "Few employees are connecting across functions. Consider identifying "
                "and empowering boundary spanners."
            )

        return {
            "health_score": health_score,
            "health_rating": self._get_health_rating(health_score),
            "total_meetings_analyzed": total_meetings,
            "cross_functional_meetings": cross_functional_meetings,
            "cross_functional_percentage": round(cross_functional_ratio * 100, 1),
            "silo_count": len(silos),
            "active_functions": active_functions,
            "top_boundary_spanners": boundary_analysis["boundary_spanners"][:5],
            "strongest_connections": matrix["strongest_connections"][:3],
            "weakest_connections": matrix["weakest_connections"][:3],
            "recommendations": recommendations,
        }

    def _get_health_rating(self, score: float) -> str:
        """Convert numeric score to rating."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Needs Improvement"
        else:
            return "Critical"
