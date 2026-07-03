"""Verifies users documents behavior, authorization rules, validation, and regression scenarios."""

import pytest

from apps.accounts.models import Permission, Role
from apps.documents.models import Document


@pytest.fixture
def admin_with_permissions(admin_user, roles):
    for code in ["users.view", "users.manage", "users.assign_role", "documents.manage"]:
        p = Permission.objects.create(code=code, name=code)
        roles[Role.ADMIN_STAFF].permissions.add(p)
    return admin_user


@pytest.mark.django_db
def test_admin_creates_user(api_client, admin_with_permissions, roles):
    api_client.force_authenticate(admin_with_permissions)
    response = api_client.post(
        "/api/v1/users",
        {
            "username": "prof1",
            "email": "prof1@example.com",
            "password": "StrongPass123!",
            "role_ids": [roles[Role.PROFESSOR].id],
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["data"]["roles"] == [Role.PROFESSOR]


@pytest.mark.django_db
def test_duplicate_user_is_rejected(api_client, admin_with_permissions, student):
    api_client.force_authenticate(admin_with_permissions)
    response = api_client.post(
        "/api/v1/users",
        {
            "username": student.username,
            "email": "new@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_role_restricted_document_visibility(
    api_client, student, admin_with_permissions, roles
):
    document = Document.objects.create(
        title="Admin policy",
        content="secret",
        access_level=Document.AccessLevel.ROLE,
        created_by=admin_with_permissions,
    )
    document.allowed_roles.add(roles[Role.ADMIN_STAFF])
    api_client.force_authenticate(student)
    assert api_client.get(f"/api/v1/documents/{document.id}").status_code == 404


@pytest.mark.django_db
def test_document_keyword_search(api_client, student, admin_with_permissions):
    Document.objects.create(
        title="Enrollment Guide",
        content="How to enroll",
        access_level=Document.AccessLevel.AUTHENTICATED,
        created_by=admin_with_permissions,
    )
    Document.objects.create(
        title="Parking",
        content="Permit",
        access_level=Document.AccessLevel.AUTHENTICATED,
        created_by=admin_with_permissions,
    )
    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/documents?keyword=enroll")
    assert response.status_code == 200
    assert len(response.data["data"]) == 1


@pytest.mark.django_db
def test_public_document_is_readable_without_authentication(api_client, admin_user):
    document = Document.objects.create(
        title="Public handbook",
        content="Public university information",
        access_level=Document.AccessLevel.PUBLIC,
        status=Document.Status.PUBLISHED,
        created_by=admin_user,
    )
    response = api_client.get(f"/api/v1/documents/{document.pk}")
    assert response.status_code == 200
    assert response.data["data"]["title"] == "Public handbook"


@pytest.mark.django_db
def test_non_public_document_is_hidden_from_anonymous_user(api_client, admin_user):
    document = Document.objects.create(
        title="Internal handbook",
        content="Internal university information",
        access_level=Document.AccessLevel.AUTHENTICATED,
        status=Document.Status.PUBLISHED,
        created_by=admin_user,
    )
    assert api_client.get(f"/api/v1/documents/{document.pk}").status_code == 404


@pytest.mark.django_db
def test_admin_registers_student_with_unique_student_number(
    api_client, admin_with_permissions, roles
):
    api_client.force_authenticate(admin_with_permissions)
    response = api_client.post(
        "/api/v1/users",
        {
            "username": "student-two",
            "email": "student-two@example.com",
            "password": "UniquePass942!",
            "first_name": "New",
            "last_name": "Student",
            "role_ids": [roles[Role.STUDENT].id],
            "profile": {"student_number": "S-2002", "phone": "555-0100"},
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["data"]["roles"] == [Role.STUDENT]
    assert response.data["data"]["profile"]["student_number"] == "S-2002"


@pytest.mark.django_db
def test_student_registration_requires_and_protects_student_number(
    api_client, admin_with_permissions, roles
):
    api_client.force_authenticate(admin_with_permissions)
    missing = api_client.post(
        "/api/v1/users",
        {
            "username": "missing-number",
            "email": "missing-number@example.com",
            "password": "UniquePass943!",
            "role_ids": [roles[Role.STUDENT].id],
            "profile": {},
        },
        format="json",
    )
    assert missing.status_code == 400
    assert "student number" in str(missing.data).lower()

    first = api_client.post(
        "/api/v1/users",
        {
            "username": "number-owner",
            "email": "number-owner@example.com",
            "password": "UniquePass944!",
            "role_ids": [roles[Role.STUDENT].id],
            "profile": {"student_number": "S-3003"},
        },
        format="json",
    )
    assert first.status_code == 201

    duplicate = api_client.post(
        "/api/v1/users",
        {
            "username": "duplicate-number",
            "email": "duplicate-number@example.com",
            "password": "UniquePass945!",
            "role_ids": [roles[Role.STUDENT].id],
            "profile": {"student_number": "s-3003"},
        },
        format="json",
    )
    assert duplicate.status_code == 400
    assert "already in use" in str(duplicate.data).lower()


@pytest.mark.django_db
def test_document_file_upload_is_extracted_published_indexed_and_retrievable(
    api_client, admin_with_permissions, student
):
    import json

    from django.core.files.uploadedfile import SimpleUploadedFile

    api_client.force_authenticate(admin_with_permissions)
    source = SimpleUploadedFile(
        "leave-policy.txt",
        b"Students may request academic leave through the university portal.",
        content_type="text/plain",
    )
    response = api_client.post(
        "/api/v1/documents/upload",
        {
            "file": source,
            "metadata": json.dumps(
                {
                    "title": "Uploaded Leave Policy",
                    "document_type": "policy",
                    "status": "published",
                    "access_level": "authenticated",
                    "knowledge_enabled": True,
                    "tags": ["leave", "student"],
                }
            ),
        },
        format="multipart",
    )

    assert response.status_code == 201
    document = Document.objects.get(pk=response.data["data"]["id"])
    assert document.title == "Uploaded Leave Policy"
    assert "academic leave" in document.content
    assert document.status == Document.Status.PUBLISHED
    assert document.knowledge_enabled is True
    assert document.index_version == 1
    assert document.versions.count() == 1

    from apps.qa.retrieval import RetrievalStrategyFactory

    results = RetrievalStrategyFactory.create("keyword").retrieve(
        student, "How can students request academic leave?"
    )
    assert document in results


@pytest.mark.django_db
def test_create_revision_updates_document_and_adds_version(
    api_client, admin_with_permissions
):
    api_client.force_authenticate(admin_with_permissions)
    created = api_client.post(
        "/api/v1/documents",
        {
            "title": "Revision policy",
            "document_type": "policy",
            "content": "Initial content",
            "access_level": "authenticated",
            "status": "published",
            "knowledge_enabled": True,
        },
        format="json",
    )
    assert created.status_code == 201
    document_id = created.data["data"]["id"]

    revised = api_client.patch(
        f"/api/v1/documents/{document_id}",
        {
            "content": "Revised content for students",
            "change_summary": "Clarified the student process",
        },
        format="json",
    )
    assert revised.status_code == 200
    document = Document.objects.get(pk=document_id)
    assert document.content == "Revised content for students"
    assert document.versions.count() == 2
    assert document.versions.first().change_summary == "Clarified the student process"


def _make_word_file(body_paragraphs, *, header=None, footer=None):
    """Build a minimal Word Open XML upload without adding a test dependency."""
    import io
    import zipfile
    from xml.sax.saxutils import escape

    def document_xml(paragraphs):
        values = "".join(
            f'<w:p><w:r><w:t xml:space="preserve">{escape(value)}</w:t></w:r></w:p>'
            for value in paragraphs
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{values}<w:sectPr/></w:body></w:document>"
        ).encode()

    def auxiliary_xml(root_name, value):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:{root_name} xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:p><w:r><w:t>{escape(value)}</w:t></w:r></w:p>"
            f"</w:{root_name}>"
        ).encode()

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", document_xml(body_paragraphs))
        if header:
            archive.writestr("word/header1.xml", auxiliary_xml("hdr", header))
        if footer:
            archive.writestr("word/footer1.xml", auxiliary_xml("ftr", footer))
    return stream.getvalue()


@pytest.mark.django_db
def test_word_upload_extracts_all_relevant_parts_and_retrieves_late_content(
    api_client, admin_with_permissions, student
):
    import json

    from django.core.files.uploadedfile import SimpleUploadedFile

    filler = [
        f"General handbook paragraph {index}." + (" filler" * 40) for index in range(80)
    ]
    target = "Scholarship appeals must be submitted within fourteen calendar days through the awards portal."
    word_bytes = _make_word_file(
        [*filler, "Scholarship appeal procedure", target],
        header="Academic Services Handbook",
        footer="Confidential footer reference 2026",
    )

    api_client.force_authenticate(admin_with_permissions)
    response = api_client.post(
        "/api/v1/documents/upload",
        {
            "file": SimpleUploadedFile(
                "student-handbook.docx",
                word_bytes,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            "metadata": json.dumps(
                {
                    "title": "Uploaded Student Handbook",
                    "status": "published",
                    "access_level": "authenticated",
                    "knowledge_enabled": True,
                }
            ),
        },
        format="multipart",
    )

    assert response.status_code == 201
    document = Document.objects.get(pk=response.data["data"]["id"])
    assert target in document.content
    assert "Academic Services Handbook" in document.content
    assert "Confidential footer reference 2026" in document.content
    assert document.index_version == 1

    from apps.qa.retrieval import RetrievalStrategyFactory, document_context

    results = RetrievalStrategyFactory.create("hybrid").retrieve(
        student, "Where do I submit a scholarship appeal and what is the deadline?"
    )
    assert results
    assert results[0].pk == document.pk
    context = document_context(results[0])
    assert target in context
    assert len(context) <= 9000
    assert target not in document.content[:12000]

    from apps.qa.prompting import PromptBuilder

    prompt = (
        PromptBuilder()
        .with_question(
            "Where do I submit a scholarship appeal and what is the deadline?"
        )
        .with_documents(results)
        .build()
    )
    assert target in prompt
