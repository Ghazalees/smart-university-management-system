# Backend API Contract — Sprints 1–3

Base path: `/api/v1`

Except for login and health, endpoints require `Authorization: Bearer <access-token>`.

## Authentication

| Method | Path | Permission | Behavior |
|---|---|---|---|
| POST | `/auth/login` | Public | Returns access/refresh tokens and user roles |
| POST | `/auth/logout` | Authenticated | Blacklists supplied refresh token |
| GET | `/auth/me` | Authenticated | Returns current profile, roles, permissions |
| GET | `/health` | Public | Checks backend and database |

Login body:

```json
{"username":"student","password":"StrongPass123!"}
```

Logout body:

```json
{"refresh":"<refresh-token>"}
```

## Users and RBAC

| Method | Path | Required permission |
|---|---|---|
| POST | `/users` | `users.manage` |
| GET | `/users` | `users.view` |
| GET | `/users/{id}` | `users.view` |
| PATCH | `/users/{id}` | `users.manage` |
| DELETE | `/users/{id}` | `users.manage` |
| PATCH | `/users/{id}/role` | `users.assign_role` |
| GET | `/roles` | Authenticated |
| GET | `/permissions` | `users.view` |

`DELETE /users/{id}` performs a soft deactivation.

Role update body:

```json
{"role_ids":[2,3]}
```

## Documents

| Method | Path | Permission |
|---|---|---|
| POST | `/documents` | `documents.manage` |
| GET | `/documents` | Authenticated and access-filtered |
| GET | `/documents/{id}` | Authenticated and access-filtered |
| PATCH | `/documents/{id}` | `documents.manage` |
| DELETE | `/documents/{id}` | `documents.manage` |
| GET | `/documents/search?keyword=...&document_type=...` | Authenticated and access-filtered |

Access levels: `public`, `authenticated`, `role`. Delete archives the record.

Example create body:

```json
{
  "title": "Registration Guide",
  "document_type": "guide",
  "content": "Students register through the university portal.",
  "access_level": "role",
  "allowed_role_ids": [1,2]
}
```

## Q&A and AI

| Method | Path | Permission |
|---|---|---|
| POST | `/questions` | `questions.create` |
| GET | `/questions/my` | Authenticated |
| GET | `/questions/{id}` | Owner or `questions.view_all` |
| POST | `/questions/{id}/answer` | `questions.answer` and object visibility |
| GET | `/questions/{id}/history` | Owner or `questions.view_all` |
| POST | `/ai/analyze-request` | Authenticated |

Question statuses: `Pending`, `Answered`, `Escalated`, `Failed`.

A response becomes `Escalated` when no accessible source documents are found or confidence is below `AI_CONFIDENCE_THRESHOLD`. AI downtime marks the question `Failed` and returns HTTP 503. Request analysis falls back to the local strategy if the AI service is unavailable.

## Response shape

Success:

```json
{"success":true,"message":"Success","data":{}}
```

Error:

```json
{"success":false,"message":"Request failed","errors":{}}
```
