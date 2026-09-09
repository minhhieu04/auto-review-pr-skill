# 🎨 Frontend Architecture, React & UI/UX Rules

This module provides universal review guidelines for Frontend applications (React, Next.js, Vue, TypeScript, CSS, Design Systems, Accessibility).

---

## 1. React Rules & Hook Semantics

### Hook Rules & Dependency Arrays
- **Exhaustive Dependencies**:
  - Ensure all variables used inside `useEffect`, `useCallback`, and `useMemo` are declared in their dependency arrays.
  - Avoid suppressing `eslint-plugin-react-hooks/exhaustive-deps` without an explicit, documented reason.
- **Stale Closures**:
  - When updating state based on previous state in callbacks or timeouts, use the updater function form: `setCount(prev => prev + 1)`.
- **Cleanup Functions**:
  - Always clean up subscriptions, `AbortController`, event listeners (`window.addEventListener`), and timers (`setInterval`) in `useEffect` return functions.

### Rendering Performance
- **Unnecessary Re-renders**:
  - Do not create inline object literals or inline arrow functions as props to heavily re-rendered child components or virtualized lists.
  - Wrap expensive calculations with `useMemo()`.
  - Memoize child components rendered inside maps with `React.memo` if parent updates frequently.
- **Key Prop Integrity**:
  - Never use array indices (`key={index}`) for dynamic, re-orderable, or filterable lists. Use unique IDs (`key={item.id}`).

---

## 2. TypeScript Best Practices

- **Strict Type Safety**:
  - Prohibit `any` usage. Replace with `unknown`, specific interfaces, or generics.
  - Use discriminated unions for modeling multi-state async operations (e.g. `{ status: 'loading' } | { status: 'success', data: T } | { status: 'error', error: Error }`).
- **Null & Undefined Guards**:
  - Use optional chaining (`obj?.property`) and nullish coalescing (`val ?? defaultVal`).
  - Do not overuse non-null assertion operator (`!`) unless guaranteed by prior validation.

---

## 3. CSS, Layout & Design System

- **Sticky Position Collisions**:
  - CSS `position: sticky` requires that NO parent element has `overflow: hidden`, `overflow: auto`, or `overflow: scroll` (other than the designated viewport scroll container).
- **Z-Index Layering**:
  - Avoid arbitrary large numbers like `z-index: 999999`. Use a defined tokenized scale (`z-dropdown`, `z-modal`, `z-tooltip`).
- **Responsive Layout**:
  - Ensure mobile and tablet viewports are accounted for (fluid widths, CSS grid / flexbox wrapping).

---

## 4. Accessibility (WCAG 2.1 AA Compliance)

- **Interactive Elements**:
  - Interactive icons/buttons without visible text MUST have `aria-label` or `title`.
  - Do not attach `onClick` handlers to non-interactive HTML tags (`div`, `span`) without `role="button"` and keyboard handlers (`onKeyDown` for Enter/Space).
- **Forms & Inputs**:
  - Every `<input>` must be associated with a `<label>` (via `htmlFor`/`id` or nesting).
- **Color Contrast**:
  - Text must meet the minimum 4.5:1 contrast ratio against its background.
