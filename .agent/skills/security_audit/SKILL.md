---
name: security-audit
description: Scans the codebase for security vulnerabilities, focusing on public AEM servlets and filter configurations.
---

# Security Audit Skill

This skill provides a set of automated checks to ensure the AEM Intelligence Engine and related components are secure. It specifically looks for potential data leaks via public servlets and overly permissive Sling filters.

## Usage

To run the security audit, execute the `security-audit.sh` script located in the `scripts` directory of this skill (or relative to the project root as configured).

```bash
./.agent/skills/security_audit/security-audit.sh
```

## Checks Performed

1.  **Public Servlet Scan**:
    -   Scans Java files in `core` for `@SlingServletPaths` or `@Component(property="sling.servlet.paths=...")`.
    -   Flags any paths that do not start with `/bin/private` (custom convention) or seem dangerously exposed without known protection.
    -   Specifically checks for `/bin/ollama` and ensures it is flagged if found (though it should be protected by filters).

2.  **Filter Hardening Check**:
    -   Checks `core` for Sling Servlet Filters.
    -   Verifies if `AuthorOnlyFilter` exists and is targeting `/bin/ollama`.

3.  **Dispatcher Config Check** (Basic):
    -   Checks `dispatcher` config files for `filters.any` to ensure `/bin/ollama` is blocked (grep check).

## Interpretation of Results

-   **PASS**: Component appears valid/secure based on static analysis.
-   **WARN**: Potential issue, requires manual review.
-   **FAIL**: Critical security vulnerability detected (e.g., config missing).
