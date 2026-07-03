"""Verifies academics behavior, authorization rules, validation, and regression scenarios."""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Permission, Profile, Role, User, UserRole
from apps.academics.models import AcademicClass, Course, Enrollment, Grade


@pytest.fixture
def academic_users(db, roles):
    permissions = {
        code: Permission.objects.create(code=code, name=code)
        for code in ["classes.create", "academics.manage"]
    }
    roles[Role.PROFESSOR].permissions.add(permissions["classes.create"])
    roles[Role.ADMIN_STAFF].permissions.add(permissions["academics.manage"])
    professor = User.objects.create_user(
        username="professor",
        email="professor@example.com",
        password="StrongPass123!",
        first_name="Ada",
        last_name="Lovelace",
    )
    Profile.objects.create(user=professor)
    UserRole.objects.create(user=professor, role=roles[Role.PROFESSOR])
    return professor


@pytest.fixture
def academic_class(student, academic_users):
    course = Course.objects.create(code="SE-401", title="Advanced Software Engineering")
    value = AcademicClass.objects.create(
        course=course,
        professor=academic_users,
        term="2026-Spring",
        section="01",
        weekday=AcademicClass.Weekday.MONDAY,
        start_time=time(9, 0),
        end_time=time(10, 30),
        location="Engineering 201",
        capacity=30,
    )
    Enrollment.objects.create(academic_class=value, student=student)
    return value


@pytest.mark.django_db
def test_professor_can_create_class_and_conflict_is_rejected(
    api_client, academic_users, academic_class
):
    api_client.force_authenticate(academic_users)
    course2 = Course.objects.create(code="SE-402", title="Architecture")
    conflict = api_client.post(
        "/api/v1/classes",
        {
            "course": course2.pk,
            "professor": academic_users.pk,
            "term": "2026-Spring",
            "section": "01",
            "weekday": AcademicClass.Weekday.MONDAY,
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "location": "Engineering 202",
            "capacity": 20,
        },
        format="json",
    )
    assert conflict.status_code == 400

    valid = api_client.post(
        "/api/v1/classes",
        {
            "course": course2.pk,
            "professor": academic_users.pk,
            "term": "2026-Spring",
            "section": "02",
            "weekday": AcademicClass.Weekday.TUESDAY,
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "location": "Engineering 202",
            "capacity": 20,
        },
        format="json",
    )
    assert valid.status_code == 201


@pytest.mark.django_db
def test_student_schedule_only_contains_enrolled_classes(
    api_client, student, academic_users, academic_class
):
    other_course = Course.objects.create(code="SE-499", title="Private Seminar")
    AcademicClass.objects.create(
        course=other_course,
        professor=academic_users,
        term="2026-Spring",
        section="01",
        weekday=AcademicClass.Weekday.FRIDAY,
        start_time=time(15, 0),
        end_time=time(16, 0),
        location="Lab",
    )
    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/classes")
    assert response.status_code == 200
    ids = {item["id"] for item in response.data["data"]}
    assert ids == {academic_class.pk}


@pytest.mark.django_db
def test_exam_must_be_in_future(api_client, academic_users, academic_class):
    api_client.force_authenticate(academic_users)
    response = api_client.post(
        "/api/v1/exams",
        {
            "academic_class": academic_class.pk,
            "title": "Midterm",
            "scheduled_at": (timezone.now() - timedelta(hours=1)).isoformat(),
            "duration_minutes": 90,
            "location": "Hall A",
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_professor_can_grade_enrolled_student_and_student_sees_only_own_grade(
    api_client, student, academic_users, academic_class, roles
):
    other = User.objects.create_user(
        username="second-student",
        email="second@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=other)
    UserRole.objects.create(user=other, role=roles[Role.STUDENT])
    Enrollment.objects.create(academic_class=academic_class, student=other)

    api_client.force_authenticate(academic_users)
    for user, score in [(student, 88), (other, 72)]:
        response = api_client.post(
            "/api/v1/grades",
            {
                "academic_class": academic_class.pk,
                "student": user.pk,
                "score": score,
                "feedback": "Good progress",
            },
            format="json",
        )
        assert response.status_code == 201

    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/grades")
    assert response.status_code == 200
    assert len(response.data["data"]) == 1
    assert response.data["data"][0]["student"] == student.pk


@pytest.mark.django_db
def test_grade_for_non_enrolled_student_is_rejected(
    api_client, academic_users, academic_class, roles
):
    outsider = User.objects.create_user(
        username="outsider",
        email="outsider@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=outsider)
    UserRole.objects.create(user=outsider, role=roles[Role.STUDENT])
    api_client.force_authenticate(academic_users)
    response = api_client.post(
        "/api/v1/grades",
        {
            "academic_class": academic_class.pk,
            "student": outsider.pk,
            "score": 90,
        },
        format="json",
    )
    assert response.status_code == 400
    assert not Grade.objects.filter(student=outsider).exists()


@pytest.mark.django_db
def test_professor_can_edit_own_class_without_reassigning_ownership(
    api_client, academic_users, academic_class, roles
):
    second_professor = User.objects.create_user(
        username="second-professor",
        email="second-professor@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=second_professor)
    UserRole.objects.create(user=second_professor, role=roles[Role.PROFESSOR])

    api_client.force_authenticate(academic_users)
    response = api_client.patch(
        f"/api/v1/classes/{academic_class.pk}",
        {
            "location": "Engineering 305",
            "capacity": 35,
            "professor": second_professor.pk,
        },
        format="json",
    )

    assert response.status_code == 200
    academic_class.refresh_from_db()
    assert academic_class.location == "Engineering 305"
    assert academic_class.capacity == 35
    assert academic_class.professor_id == academic_users.pk


@pytest.mark.django_db
def test_class_performance_report_lists_grades_ungraded_students_and_feedback(
    api_client, student, academic_users, academic_class, roles
):
    ungraded_student = User.objects.create_user(
        username="ungraded-student",
        email="ungraded@example.com",
        password="StrongPass123!",
        first_name="Grace",
        last_name="Hopper",
    )
    Profile.objects.create(user=ungraded_student)
    UserRole.objects.create(user=ungraded_student, role=roles[Role.STUDENT])
    Enrollment.objects.create(academic_class=academic_class, student=ungraded_student)
    Grade.objects.create(
        academic_class=academic_class,
        student=student,
        score=88,
        feedback="Strong architecture work",
        graded_by=academic_users,
    )

    api_client.force_authenticate(academic_users)
    response = api_client.get(f"/api/v1/classes/{academic_class.pk}")

    assert response.status_code == 200
    report = response.data["data"]["report"]
    assert report["graded_count"] == 1
    assert report["ungraded_count"] == 1
    assert report["average"] == 88.0
    assert report["minimum"] == 88.0
    assert report["maximum"] == 88.0
    assert len(report["students"]) == 2

    rows = {row["student_id"]: row for row in report["students"]}
    assert rows[student.pk]["score"] == 88.0
    assert rows[student.pk]["feedback"] == "Strong architecture work"
    assert rows[student.pk]["has_grade"] is True
    assert rows[ungraded_student.pk]["score"] is None
    assert rows[ungraded_student.pk]["feedback"] == ""
    assert rows[ungraded_student.pk]["has_grade"] is False


@pytest.mark.django_db
def test_student_cannot_access_class_performance_report(
    api_client, student, academic_class
):
    api_client.force_authenticate(student)
    response = api_client.get(f"/api/v1/classes/{academic_class.pk}")

    assert response.status_code == 403


@pytest.mark.django_db
def test_class_capacity_cannot_drop_below_current_enrollment(
    api_client, student, academic_users, academic_class, roles
):
    second_student = User.objects.create_user(
        username="capacity-student",
        email="capacity@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=second_student)
    UserRole.objects.create(user=second_student, role=roles[Role.STUDENT])
    Enrollment.objects.create(academic_class=academic_class, student=second_student)

    api_client.force_authenticate(academic_users)
    response = api_client.patch(
        f"/api/v1/classes/{academic_class.pk}",
        {"capacity": 1},
        format="json",
    )

    assert response.status_code == 400
    assert "capacity" in str(response.data).lower()


@pytest.mark.django_db
def test_duplicate_student_enrollment_returns_validation_error(
    api_client, admin_user, academic_users, academic_class, student
):
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        "/api/v1/enrollments",
        {"academic_class": academic_class.pk, "student": student.pk},
        format="json",
    )
    assert response.status_code == 400
    assert "already enrolled" in str(response.data).lower()
