# ADR: W05 local browser integration harness

Date: 2026-11-11

## Status

Accepted for test-only local integration. This is not a production listener, deployment path, or OpenCTI integration.

## Context

The reviewed UI snapshot uses same-origin `/api/drafts*` requests. The backend's production settings correctly require an HTTPS portal origin, while a local browser run needs an HTTP loopback origin. The harness also needs a real signed JWT, server-side role lookup, SQLite state, deterministic cleanup, and a fault mode that proves a successful decision is not retried when the refresh fails.

## Decision

- Keep `Settings.from_env()` and direct `Settings(...)` HTTPS-only. A private, guarded constructor is reachable only through `tools.local_integration.local_settings.make_local_settings()` and accepts exactly `http://127.0.0.1:<port>`.
- Run Uvicorn 0.54.0 on a random `127.0.0.1` port, a production Next build on a second loopback port, and the Node same-origin gateway on a third. All processes are owned by `LocalRun` and have a TTL.
- Generate an ephemeral RSA key and signed JWT in memory. The API verifies signature, issuer, audience, expiry and subject through the real `AccessJwtVerifier`; roles remain server-side. The gateway removes caller-supplied authorization and injects only the scenario token.
- Preserve the browser's Origin. Never synthesize or rewrite it. Proxy only the reviewed `/api/drafts*` routes, strip hop-by-hop headers, buffer a bounded request body, preserve end-to-end response headers including repeated `Set-Cookie`, never retry, and return a sanitized `503` on timeout/upstream failure.
- Reject an invalid request target with a sanitized `400`. If an upstream fails before response headers, return a sanitized `503`; if it fails after headers, close the incomplete downstream response. Client disconnects destroy the one owned upstream request. No path retries a POST.
- Use a fresh temporary SQLite database and four synthetic drafts for each run. Scenarios are a fixed allowlist. Cleanup attempts each owned child and API resource independently, removes the run's temporary directory only after the API thread has stopped, reports aggregated failures, and leaves unfinished resources retryable by a later `close()` call.

## Consequences

The harness can exercise the unchanged UI against the real local API contract over a browser-safe same origin without weakening the production HTTPS rule. It deliberately does not cover trusted local HTTPS, external JWKS, a lab, real secrets, OpenCTI, deployment, or production process supervision.

## Verification contract

The automated matrix covers authenticated list/detail, approve/reject, exact-once audit, self-review denial, role denial, missing/expired/wrong-signature JWT, Origin and content-type enforcement, malformed roles, no-store, and POST-success/refresh-503 without retry. Browser checks cover the live queue, approve, reject, sample mode, and the visible refresh-failure state.
