# 🧪 Testing, Resilience & Edge-Case Rules

This module provides universal guidelines for automated testing quality, async reliability, and resilient error recovery.

---

## 1. Testing Quality & Anti-Patterns

### Never Test Mock Behavior
- **The Golden Rule**: Tests must verify the **real behavior and output** of your code, NOT the return values configured on mocks.
  - If a test asserts `mock_service.do_something.assert_called_with(...)` without verifying the outcome of the function under test, it tests implementation details, not correctness.
- **Never Add Test-Only Methods to Production Classes**:
  - Production code must not contain helper flags or methods specifically created to satisfy tests (e.g. `is_in_test_mode`).

### Coverage of Edge Cases
- Test empty states: empty arrays (`[]`), null parameters (`None`), 0 values, extreme lengths.
- Test error paths: simulate network timeouts, database errors, and unauthorized responses.

---

## 2. Flaky Tests & Condition-Based Waiting

- **No Arbitrary Delays**:
  - Prohibit hardcoded `time.sleep(5)` or `setTimeout(..., 3000)` in unit/integration/E2E tests.
  - Replace arbitrary timeouts with **condition polling**:
    - *Playwright*: `expect(locator).toBeVisible()` or `page.waitForResponse(...)`.
    - *Jest/Testing Library*: `waitFor(() => expect(...).toBeInTheDocument())`.
    - *Python*: `tenacity` retry or polling loop with short interval and timeout.

---

## 3. Resilience & Concurrency

- **Race Conditions**:
  - Flag concurrent writes to shared state without synchronization, locks, or database transactions (`select_for_update()`).
- **Timeouts & Deadlines**:
  - Every external HTTP request must specify an explicit timeout (e.g. `requests.get(url, timeout=10)`).
- **Graceful Degradation**:
  - When non-critical third-party services fail (analytics, notification services), the primary user flow should continue without interruption.
