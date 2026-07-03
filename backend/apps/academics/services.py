"""Contains reusable business logic for academic classes, enrollments, exams, grades, and progress."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Avg, Q
from django.utils import timezone

from .models import (
    AcademicClass,
    Course,
    CoursePrerequisite,
    Enrollment,
    Grade,
    ProgramRequirement,
    StudentAcademicGoal,
)


class DegreeProgressService:
    PASS_SCORE = Decimal("50")

    @classmethod
    def build(cls, student):
        requirements = ProgramRequirement.objects.select_related("course").filter(
            department=student.department, is_required=True
        )
        if not requirements.exists() and student.department_id:
            requirements = [
                type(
                    "FallbackRequirement",
                    (),
                    {
                        "course": course,
                        "category": ProgramRequirement.Category.CORE,
                        "minimum_score": cls.PASS_SCORE,
                        "recommended_term": None,
                    },
                )
                for course in Course.objects.filter(
                    department=student.department, is_active=True
                )
            ]
        completed_grades = {
            grade.academic_class.course_id: grade
            for grade in Grade.objects.select_related("academic_class__course").filter(
                student=student
            )
        }
        active_course_ids = set(
            Enrollment.objects.filter(
                student=student, academic_class__is_active=True
            ).values_list("academic_class__course_id", flat=True)
        )
        rows = []
        completed_credits = 0
        total_credits = 0
        by_category = {}
        for requirement in requirements:
            course = requirement.course
            grade = completed_grades.get(course.pk)
            threshold = Decimal(str(requirement.minimum_score))
            status = (
                "completed"
                if grade and grade.score >= threshold
                else "in_progress"
                if course.pk in active_course_ids
                else "remaining"
            )
            total_credits += course.credits
            if status == "completed":
                completed_credits += course.credits
            category = requirement.category
            bucket = by_category.setdefault(
                category,
                {"total": 0, "completed": 0, "credits": 0, "completed_credits": 0},
            )
            bucket["total"] += 1
            bucket["credits"] += course.credits
            if status == "completed":
                bucket["completed"] += 1
                bucket["completed_credits"] += course.credits
            rows.append(
                {
                    "course_id": course.pk,
                    "code": course.code,
                    "title": course.title,
                    "credits": course.credits,
                    "category": category,
                    "status": status,
                    "score": float(grade.score) if grade else None,
                    "minimum_score": float(threshold),
                    "recommended_term": requirement.recommended_term,
                }
            )
        average = Grade.objects.filter(student=student).aggregate(value=Avg("score"))[
            "value"
        ]
        percentage = (
            round((completed_credits / total_credits * 100), 1) if total_credits else 0
        )
        return {
            "completed_credits": completed_credits,
            "total_credits": total_credits,
            "percentage": percentage,
            "average_score": float(average) if average is not None else None,
            "categories": by_category,
            "requirements": rows,
        }


@dataclass(frozen=True)
class AcademicRecommendation:
    code: str
    title: str
    description: str
    priority: str
    action_url: str
    metadata: dict


class RecommendationStrategy(ABC):
    @abstractmethod
    def recommend(self, student, progress): ...


class MissingRequirementStrategy(RecommendationStrategy):
    def recommend(self, student, progress):
        remaining = [
            row for row in progress["requirements"] if row["status"] == "remaining"
        ]
        return [
            AcademicRecommendation(
                f"requirement-{row['course_id']}",
                f"Plan {row['code']}",
                f"{row['title']} is still required for degree completion.",
                "high" if row["category"] in {"core", "specialized"} else "medium",
                "/academics/classes",
                {"course_id": row["course_id"], "credits": row["credits"]},
            )
            for row in remaining[:4]
        ]


class PrerequisiteStrategy(RecommendationStrategy):
    def recommend(self, student, progress):
        completed = {
            row["course_id"]
            for row in progress["requirements"]
            if row["status"] == "completed"
        }
        results = []
        for link in CoursePrerequisite.objects.select_related(
            "course", "prerequisite"
        ).filter(course__department=student.department):
            if (
                link.course_id not in completed
                and link.prerequisite_id not in completed
            ):
                results.append(
                    AcademicRecommendation(
                        f"prerequisite-{link.course_id}-{link.prerequisite_id}",
                        f"Complete {link.prerequisite.code} first",
                        f"{link.prerequisite.title} unlocks {link.course.title}.",
                        "high",
                        "/academics/classes",
                        {
                            "course_id": link.course_id,
                            "prerequisite_id": link.prerequisite_id,
                        },
                    )
                )
        return results[:3]


class PerformanceStrategy(RecommendationStrategy):
    def recommend(self, student, progress):
        average = progress.get("average_score")
        goal, _ = StudentAcademicGoal.objects.get_or_create(student=student)
        results = []
        if average is not None and average < float(goal.target_gpa):
            gap = round(float(goal.target_gpa) - average, 1)
            results.append(
                AcademicRecommendation(
                    "gpa-gap",
                    "Close your target gap",
                    f"Your current average is {average:.1f}. You need about {gap:.1f} more points to reach your target.",
                    "medium",
                    "/academics/grades",
                    {"current": average, "target": float(goal.target_gpa), "gap": gap},
                )
            )
        active_credits = sum(
            enrollment.academic_class.course.credits
            for enrollment in Enrollment.objects.select_related(
                "academic_class__course"
            ).filter(student=student, academic_class__is_active=True)
        )
        if active_credits > goal.preferred_max_credits:
            results.append(
                AcademicRecommendation(
                    "course-load",
                    "Review your course load",
                    f"You are carrying {active_credits} credits, above your preferred limit of {goal.preferred_max_credits}.",
                    "high",
                    "/academics/classes",
                    {
                        "active_credits": active_credits,
                        "preferred": goal.preferred_max_credits,
                    },
                )
            )
        return results


class AcademicRecommendationService:
    def __init__(self, strategies=None):
        self.strategies = strategies or [
            MissingRequirementStrategy(),
            PrerequisiteStrategy(),
            PerformanceStrategy(),
        ]

    def build(self, student):
        progress = DegreeProgressService.build(student)
        results = []
        for strategy in self.strategies:
            results.extend(strategy.recommend(student, progress))
        priority_order = {"high": 0, "medium": 1, "low": 2}
        results.sort(
            key=lambda item: (priority_order.get(item.priority, 3), item.title)
        )
        return progress, [item.__dict__ for item in results[:8]]


class ScheduleSuggestionService:
    START_HOURS = (8, 9, 10, 11, 13, 14, 15, 16, 17)

    @classmethod
    def suggest(cls, professor, term, duration_minutes=90, weekdays=None, location=""):
        weekdays = weekdays or [1, 2, 3, 4, 5]
        candidates = []
        for weekday in weekdays:
            for hour in cls.START_HOURS:
                starts = time(hour=hour)
                ends_dt = datetime.combine(timezone.localdate(), starts) + timedelta(
                    minutes=duration_minutes
                )
                ends = ends_dt.time()
                professor_conflict = AcademicClass.objects.filter(
                    professor=professor,
                    term=term,
                    weekday=weekday,
                    start_time__lt=ends,
                    end_time__gt=starts,
                    is_active=True,
                ).exists()
                room_conflict = (
                    bool(location)
                    and AcademicClass.objects.filter(
                        location__iexact=location,
                        term=term,
                        weekday=weekday,
                        start_time__lt=ends,
                        end_time__gt=starts,
                        is_active=True,
                    ).exists()
                )
                if professor_conflict or room_conflict:
                    continue
                adjacent = (
                    AcademicClass.objects.filter(
                        professor=professor,
                        term=term,
                        weekday=weekday,
                        is_active=True,
                    )
                    .filter(Q(end_time=starts) | Q(start_time=ends))
                    .count()
                )
                score = 100 - adjacent * 10 - (10 if hour == 8 or hour >= 17 else 0)
                candidates.append(
                    {
                        "weekday": weekday,
                        "start_time": starts.strftime("%H:%M"),
                        "end_time": ends.strftime("%H:%M"),
                        "score": score,
                        "reason": "Conflict-free slot"
                        if adjacent == 0
                        else "Conflict-free with adjacent class",
                    }
                )
        return sorted(
            candidates,
            key=lambda row: (-row["score"], row["weekday"], row["start_time"]),
        )[:12]
