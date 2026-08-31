# ADR-007: Inter-Process Communication (IPC) Strategy

**Status:** Accepted — Implemented (Phase 01 Epic 1.2)

**Date:** 2026-07-23
**Implementation Date:** 2026-07-29

**Decision Makers:** Project Architecture Team

---

# Context

The Document-Management-RAG-Graph-Agent separates the presentation layer from the backend application services.

The frontend is responsible for user interaction and presentation, while the backend manages business logic, AI orchestration, indexing, search, storage coordination, and other application services.

These components must communicate through a secure, maintainable, and well-defined mechanism.

Allowing arbitrary communication between the frontend and backend would increase coupling, reduce maintainability, and create unnecessary security risks.

The architecture therefore requires a standardized communication strategy.

---

# Decision

The Document-Management-RAG-Graph-Agent will use a command-based Inter-Process Communication (IPC) architecture.

All communication between the frontend and backend will occur through explicitly defined IPC interfaces.

The frontend must never access backend internals directly.

Backend services expose only approved commands that represent application use cases.

All IPC requests and responses should follow standardized contracts.

---

# Rationale

A command-based IPC architecture provides a clear boundary between presentation and business logic.

This approach improves maintainability, simplifies testing, enhances security, and ensures that backend functionality remains accessible only through approved interfaces.

It also aligns with the layered architecture and capability-based organization adopted throughout the project.

---

# IPC Responsibilities

The IPC layer is responsible for:

* Receiving frontend requests.
* Validating request contracts.
* Routing requests to the appropriate application service.
* Returning standardized responses.
* Translating backend errors into user-safe responses.
* Preventing unauthorized backend access.

The IPC layer is not responsible for implementing business logic.

---

# Communication Principles

All IPC communication should follow these principles:

* Explicit request and response contracts.
* Strongly typed payloads whenever practical.
* No direct database access from the frontend.
* No direct AI provider access from the frontend.
* Stateless request handling where appropriate.
* Clear separation between transport and business logic.

Business rules should remain within the backend application services.

---

# Security Considerations

The IPC boundary is considered a security boundary.

The architecture should ensure that:

* Only approved commands are exposed.
* Input validation occurs before business processing.
* Sensitive information is not exposed unnecessarily.
* Internal exceptions are translated into safe responses.
* Unauthorized operations are rejected.

Frontend applications should never receive direct access to backend implementation details.

---

# Alternatives Considered

## Direct Backend Access

Advantages:

* Simple implementation.
* Minimal architectural layers.

Disadvantages:

* Tight coupling.
* Poor security.
* Difficult maintenance.
* Limited scalability.

This option was rejected.

---

## Generic Message Passing

Advantages:

* Flexible communication.

Disadvantages:

* Weak contracts.
* Difficult validation.
* Inconsistent behavior.
* Harder debugging.

This option was rejected.

---

## Command-Based IPC

Advantages:

* Clear interfaces.
* Strong separation of concerns.
* Improved security.
* Better maintainability.
* Easier testing.
* Consistent communication model.

This option was selected.

---

# Consequences

## Positive

* Clearly defined communication boundaries.
* Reduced coupling between frontend and backend.
* Improved application security.
* Easier testing of business logic.
* Consistent request handling.
* Better long-term maintainability.

## Negative

* Additional implementation layer.
* Requires maintenance of request and response contracts.
* Slight increase in development effort.

These trade-offs are acceptable given the architectural goals of the project.

---

# Implementation Impact

Implementation should ensure that:

* Every IPC command represents a business use case.
* Backend services remain independent of transport mechanisms.
* Request validation occurs before business logic execution.
* Responses follow consistent structures.
* Error handling is standardized across all IPC commands.
* Logging and diagnostics are implemented at the IPC boundary where appropriate.

---

# Related Documents

* `docs/architecture/application-layers.md`
* `docs/architecture/system-overview.md`
* `docs/architecture/technology-stack.md`

---

# Implementation

## Transport mechanism (Phase 01)

The IPC channel is implemented as a two-layer stack:

```
React (TypeScript)
     │
  IPCClient.ts                 ← single call-site; no component calls invoke() directly
     │
  @tauri-apps/api/core invoke  ← Tauri JS ↔ Rust bridge
     │
  Tauri Rust command handler   ← thin passthrough; validates command exists
     │
  reqwest HTTP POST            ← loopback (127.0.0.1:{dynamic-port})
     │
  Python FastAPI handler       ← business logic lives here
```

### Sidecar startup protocol

The Tauri process spawns `python -m enterprise_ai_companion` as a child process
on application launch. The Python process prints `READY:{port}` to stdout once
uvicorn is listening. The Rust layer reads this signal, stores the port in
`AppState`, and emits a `sidecar-ready` event to the frontend. IPC commands
that proxy to the sidecar will reject with an error until the port is known.

### Current commands

| Tauri command | HTTP route | Description |
|---|---|---|
| `health_check` | `GET /health` | Liveness probe; used by the frontend to verify sidecar is reachable |

### TypeScript boundary

All `invoke()` calls are routed through `frontend/src/services/ipc/IPCClient.ts`.
No component or service imports `@tauri-apps/api/core` directly.

The `waitForSidecar()` utility in `IPCClient.ts` returns a promise that resolves
when `sidecar-ready` fires, allowing startup sequences to gate on sidecar
readiness without polling.

### Port selection

The sidecar selects a free port at startup using `socket.bind(("127.0.0.1", 0))`.
This avoids hardcoded port conflicts. The port is communicated to Tauri via stdout
and is not persisted between application launches.

---

# Notes

This decision establishes the communication strategy between the frontend and backend of the Document-Management-RAG-Graph-Agent.

Future communication mechanisms should preserve the same architectural principles, ensuring that presentation and business logic remain cleanly separated regardless of the underlying transport technology.
