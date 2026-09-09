# 🛡️ Security, Secrets & Defense-in-Depth Rules

This module provides universal security review guidelines covering OWASP Top 10, Secrets Management, and Multi-layer Validation.

---

## 1. Secrets & Credentials Detection (🔴 Critical)

Never commit sensitive credentials into git history:
- **Patterns to Flag**:
  - API Keys, Bearer tokens, JWT secrets: `(api_key|secret|token|password|auth_token)\s*=\s*['"][A-Za-z0-9_\-]{8,}['"]`
  - Cloud provider credentials: AWS keys (`AKIA[0-9A-Z]{16}`), Google API keys (`AIza[0-9A-Za-z-_]{35}`), Private Keys (`-----BEGIN RSA PRIVATE KEY-----`)
  - Connection strings with embedded passwords: `postgres://user:password@host/db`
- **Resolution**:
  - Use environment variables (`os.environ.get()`, `process.env`) or secret managers (Vault, AWS Secrets Manager, GCP Secret Manager).

---

## 2. Injection Attacks & Input Sanitization

- **SQL Injection**:
  - Prohibit raw string concatenation / f-strings in queries:
    - ❌ `cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")`
    - ✅ `cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])`
- **XSS (Cross-Site Scripting)**:
  - Avoid `dangerouslySetInnerHTML` in React or raw HTML unescaping without sanitization libraries (DOMPurify).
- **Command Injection**:
  - Prohibit `os.system()` or `subprocess.run(shell=True)` with user-supplied arguments. Use parameter lists instead.

---

## 3. Defense-in-Depth Validation

Validate at every layer data passes through:
1. **API Boundary**: Reject malformed payloads immediately with schema validation (Pydantic, DTOs, Serializers, Zod).
2. **Business Logic Layer**: Check business rules, object states, and domain constraints independently.
3. **Database Layer**: Rely on database-level constraints (Foreign Keys, Unique constraints, Check constraints, NOT NULL).

---

## 4. Authorization & Privilege Escalation

- **IDOR / BOLA**: Verify that the user executing an update/delete action is authorized to modify that specific resource entity.
- **Mass Assignment**: Ensure request bodies cannot overwrite sensitive fields (e.g. `is_admin`, `role`, `balance`, `verified`).
