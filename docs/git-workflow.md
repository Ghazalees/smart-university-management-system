# GitHub Workflow

## Branches created for this delivery

- `feature/sprint-1-backend`
- `feature/sprint-2-backend`
- `feature/sprint-3-backend`
- `main`

Each sprint branch has a focused implementation commit and is merged into `main` with `--no-ff`, preserving sprint boundaries in history.

## Recommended remote workflow

1. Protect `main` and disallow direct pushes.
2. Branch from the latest `main` using `feature/sprint-N-topic`.
3. Use Conventional Commits: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
4. Open a pull request with backlog references, migration notes, API changes, and test evidence.
5. Require backend CI and AI-service CI.
6. Require one review and resolved conversations.
7. Merge with a merge commit so sprint/feature history remains visible.
8. Tag accepted increments, for example `sprint-3-backend-complete`.

## Suggested pull request order

- PR 1: Sprint 1 foundation and authentication.
- PR 2: Sprint 2 users/RBAC/documents.
- PR 3: Sprint 3 AI/Q&A and architecture documentation.

## Commands to reproduce the local merge history

```bash
git checkout main
git merge --no-ff feature/sprint-1-backend -m "merge: sprint 1 backend foundation"
git merge --no-ff feature/sprint-2-backend -m "merge: sprint 2 user RBAC and document management"
git merge --no-ff feature/sprint-3-backend -m "merge: sprint 3 AI Q&A and architecture"
git tag -a sprint-3-backend-complete -m "Backend through Sprint 3"
```
