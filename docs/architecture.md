# Sprint 1 Architecture Notes

## High-level architecture

The system follows a modular, service-oriented architecture:

- **Nginx/API Gateway** receives external HTTP traffic and routes requests to the correct service.
- **React Frontend** serves the user interface.
- **Django Backend** owns authentication, RBAC, documents, and core university APIs under `/api/v1`.
- **FastAPI AI Service** exposes AI-related endpoints independently so future AI workloads can scale without coupling to the Django backend.
- **SQLite development database** stores initial Sprint 1 data models and can be replaced by PostgreSQL in later environments.

## Backend modular structure

Django apps are separated by responsibility:

- `apps.accounts`: authentication, roles, permissions, dashboards, token auth.
- `apps.core`: health check, standardized responses, centralized exception handling, request id middleware, request logging, reusable validators, shared service result object.
- `apps.documents`: document model, serializer, permission guard, service layer, CRUD/search API, and tests.

## API response standard

All new APIs should use this response envelope:

```json
{
  "success": true,
  "message": "Request completed successfully.",
  "data": {},
  "meta": {}
}
```

Errors use:

```json
{
  "success": false,
  "message": "Request failed.",
  "errors": {},
  "meta": {}
}
```

## Sprint 1 completed issue coverage

- #8 Django core and API routing
- #9 Centralized configuration and environment management
- #10 Modular Django service-layer architecture
- #11 Centralized backend error handling
- #12 Backend logging and error logging
- #13 Initial document storage module
- #14 Request validation infrastructure
- #15 Standardized backend API response format
- #16 Reusable backend middleware layer
- #17 Backend testing infrastructure and initial API tests
- #18 Backend Docker development environment
- #19 GitHub Actions CI pipeline
