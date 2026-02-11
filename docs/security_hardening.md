# Security Hardening Guide: AEM Intelligence Engine

This guide outlines the security measures and configurations required to strictly control access to the AEM Intelligence Engine.

## 1. Dispatcher Configuration (CRITICAL)

The Intelligence Engine exposes endpoints under `/bin/ollama/*`. These **MUST** be blocked on the Publish tier via Dispatcher filters to prevent public access.

### `dispatcher/src/conf.dispatcher.d/filters/filters.any`

Add the following rule to explicitly DENY access to the AI endpoints on Publish:

```
# Block AEM Intelligence Engine endpoints on Publish
/0900 { /type "deny" /url "/bin/ollama/*" }
```

> [!WARNING]
> If you are running a hybrid setup where authenticated users on Publish need access, you must ensure the underlying `AuthorOnlyFilter` is correctly configured with adequate group checks, and `Dispatcher` is configured to allow authorized requests (e.g., via session management). However, the default recommendation is **DENY** on Publish.

## 2. OSGi Configuration

The Engine is controlled via `com.aem.intelligence.core.conf.AIConfiguration`.

- **Author Tier**: Enabled by default.
- **Publish Tier**: Disabled by default (implicit, as config is only present in `config.author`).

To explicitly disable on Publish (recommended safety net), create:
`ui.apps/src/main/content/jcr_root/apps/aem-intelligence/config.publish/com.aem.intelligence.core.conf.AIConfiguration.config`

```properties
enabled=B"false"
```

## 3. Java Security Filter

The `AuthorOnlyFilter` provides a second line of defense at the application level.

- **Path**: `/bin/ollama/*`
- **Logic**:
    1. Checks if `AIConfiguration` is enabled. If not -> `403 Forbidden`.
    2. Checks if user is authenticated. If not -> `403 Forbidden`.
    3. Checks if user is a member of `authors` or `administrators` (configurable). If not -> `403 Forbidden`.

## 4. Best Practices

- **Never** expose API keys or internal Ollama URLs to the client-side.
- The `OllamaServlet` acts as a proxy; ensure it does not blindly forward all headers or parameters.
- regularly audit user group memberships.
