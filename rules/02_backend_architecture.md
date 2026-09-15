# ⚙️ Backend Architecture & Database Rules

This module provides universal review guidelines for Backend services (Django, FastAPI, NestJS, Express, Go, Java) and Database operations.

---

## 1. Database & ORM Performance

### N+1 Query Prevention & Strict Boundaries
- **Definition of N+1 Problem**:
  - An N+1 query problem occurs **ONLY** when a database query is repeatedly executed inside a loop/iteration or GraphQL resolver for each element of a collection (1 primary query + N secondary queries).
- **Proper Solutions**:
  - *Django*: Use `select_related()` for ForeignKey/OneToOne, `prefetch_related()` for ManyToMany/Reverse FK.
  - *TypeORM / Prisma*: Use `relations` or `include` rather than querying in `map()`.
  - *SQLAlchemy*: Use `joinedload()` or `selectinload()`.
  - *GraphQL Resolvers*: Implement DataLoader patterns for resolving nested fields.
- **Bulk Operations**:
  - Prefer `bulk_create()` / `bulk_update()` over saving objects in an iteration.
- **Unbounded Queries**:
  - Every collection query must have pagination (`limit`/`offset` or cursor-based) or strict filters.

### 🚫 STRICT GUARDRAILS: WHAT IS NOT AN N+1 QUERY (DO NOT FLAG!)
Reviewers (both AI and automated subagents) must **NEVER** flag the following as N+1 queries:
1. **In-Memory Data Structure Lookups**:
   - Python dictionary accesses like `data.get(...)`, `request.data.get(...)`, `params.get(...)`, `dict[key]` are memory lookups, **NOT database queries**.
2. **Single / Standalone ORM Queries**:
   - A single `Model.objects.get(...)`, `Model.objects.filter(...)`, `Model.objects.create()`, or `Model.objects.update()` executed once in a view, service, or function outside of a loop executes exactly **1 query**. It is impossible for a single query to be an N+1 problem.
3. **Queries with Existing Prefetching / Joins**:
   - Do NOT flag queries that already include `select_related()` or `prefetch_related()`, even if chained across multiple lines.
4. **Batch Lookups with `__in`**:
   - Queries like `Model.objects.filter(id__in=id_list)` execute a single SQL query with `WHERE id IN (...)`. This is a best-practice batch query, not an N+1 issue.
5. **No Evidence of Loop**:
   - If you cannot point to an explicit iteration construct (`for`, `while`, list comprehension) surrounding the database access, **DO NOT FLAG** as N+1.

### Migration Safety & Database Locks
- **Table Locks**: Avoid adding non-nullable columns without defaults on high-traffic tables.
- **Index Creation**: In PostgreSQL, ensure heavy indexes are created `CONCURRENTLY` (or via non-blocking migrations).
- **Destructive Operations**: Flag `ALTER TABLE DROP COLUMN` or `DROP TABLE` without multi-step deprecation strategy.
- **Lock Contention**: Keep transactions as short as possible; never make network/HTTP calls inside a database transaction.

---

## 2. API Design & HTTP Semantics

- **RESTful Conventions**:
  - `GET` must be idempotent and side-effect free.
  - `POST` creates resources (returns `201 Created` with resource location).
  - `PUT`/`PATCH` updates resources (returns `200 OK` or `204 No Content`).
  - `DELETE` removes resources (returns `204 No Content`).
- **Error Responses**:
  - Return standardized error payload (`{"error": {"code": "...", "message": "..."}}`).
  - Never return stack traces or raw internal database exceptions to the client.
- **Validation**:
  - Validate all payloads at the controller/view boundary (DTOs, Pydantic, DRF Serializers, Zod).

---

## 3. Authentication & Authorization

- **Endpoint Protection**:
  - Verify all newly added endpoints have appropriate guards/decorators (`@login_required`, `@permission_required`, `@UseGuards(JwtAuthGuard)`).
  - Check for IDOR (Insecure Direct Object Reference): verify user owns or has permission to access the requested object ID (`obj.owner_id == request.user.id`).
- **Token Handling**:
  - Never accept expired or unverified JWTs.
  - Keep sensitive claims out of JWT payloads.

---

## 4. Code Health & Refactoring Patterns

- **Function Complexity**:
  - Functions should ideally be < 30 lines. Nesting depth should not exceed 3 levels.
  - Extract complex conditional logic into helper functions with descriptive boolean names.
- **Exception Handling**:
  - Never use bare `except:` or `catch (e) {}` without logging or re-raising.
  - Catch specific exception classes (`ValueError`, `DoesNotExist`, `NotFoundException`).
- **Null Safety**:
  - Guard against `None`/`null`/`undefined` when reading optional payload fields or database query results.
