# Phase 00: Desktop Companion Experience

**Phase:** 00

**Status:** Complete

**Estimated Duration:** 1 Day

---

# Purpose

Phase 00 establishes the visual identity and primary interaction model of the Enterprise AI Companion.

The Enterprise AI Companion is not a chat application that lives in a window. It is a **desktop-native AI companion** — a persistent, context-aware presence that understands the user's work and is immediately accessible from anywhere within Windows.

The Living Orb and Glass Prompt form the application's primary interaction surface. The Workspace provides an expanded environment for longer conversations and advanced capabilities. Beneath these surfaces lies a Context Engine that understands what the user is working on, a Retrieval Broker that can locate knowledge across local files and cloud storage, and a Project Knowledge Layer that accumulates understanding over time.

Every major capability introduced in Version 1 should be accessible directly or indirectly through this companion interface.

The objective of this phase is **not** to build intelligence, but to build the experience.

At the end of this phase, users should be able to launch the application and immediately interact with a polished companion interface using mock responses.

---

# Objectives

Upon completion of this phase, the application should provide:

* Desktop application shell
* Modern user interface
* Living Orb
* Glass Prompt
* Desktop Presence Layer
* Responsive Workspace
* Conversation area
* Message input
* Mock companion responses
* Theme support
* Navigation foundation
* Clean architecture service layer
* AI provider abstraction

No backend services or real AI providers are required during this phase.

---

# Product Pillars

The Enterprise AI Companion is built around five core pillars. Each pillar represents a distinct capability domain that the platform must support.

## Desktop Companion

A persistent, always-accessible presence on the Windows desktop.

The companion appears through the Living Orb and Glass Prompt. It is available from any application, at any moment, without requiring the user to switch context. This is the primary interaction model for Version 1.

---

## Context Intelligence

The ability to understand what the user is working on without being told explicitly.

The Context Engine observes the active workspace — open documents, recent activity, project folders — and uses this signal to improve retrieval relevance and response quality. Context intelligence transforms the companion from a generic chat interface into a knowledgeable collaborator.

---

## Cross-Platform Retrieval

The ability to search and retrieve knowledge from multiple sources through a single interface.

The Retrieval Broker abstracts access to local files and cloud storage connectors. In Version 1, two connectors are supported: the Local File Connector and the OneDrive Connector. Additional connectors may be added in future phases without changing the retrieval interface.

---

## Project Knowledge

The ability to accumulate and organize knowledge associated with specific projects over time.

The Project Knowledge Layer allows the companion to maintain awareness of project goals, decisions, and history. This accumulated context enables increasingly relevant assistance as the user continues working within a project.

---

## Workspace

An expanded environment for extended interactions, structured knowledge exploration, and deeper engagement with retrieved content.

The Workspace surfaces when a conversation or task exceeds the lightweight interaction model of the Glass Prompt. It provides conversation history, document references, and access to project knowledge without losing the active conversational thread.

---

# Experience Principles

These principles govern how the Enterprise AI Companion behaves from the user's perspective.

## Desktop First, Workspace Second

The primary interaction should never require opening the full workspace. Quick questions, document lookups, and brief exchanges should complete entirely within the Glass Prompt. The Workspace is an escalation path, not the default.

---

## Context Before Conversation

The companion should understand what the user is working on before the user explains it. Retrieved results and generated responses should reflect active context whenever possible. Users should never need to re-state what they are doing.

---

## Unified Knowledge

The user should experience a single search surface regardless of where their files live. Local files and OneDrive documents should surface in the same response. The distinction between storage locations should be invisible to the user.

---

## Progressive Disclosure

Lightweight interactions remain lightweight. Complexity is introduced only when the user needs it. The companion should never present more interface than the current task requires.

---

## Calm Intelligence

The companion should feel present and capable without demanding attention. State changes, notifications, and transitions should be visually calm. The orb communicates system state through subtle visual cues rather than interruptions.

---

## Confidence Transparency

When the companion retrieves or generates content, it should be clear what it knows and how confident it is. Uncertain responses should be presented as such. Fabricated context is worse than acknowledged uncertainty.

---

# Prerequisites

Before beginning:

* Project repository created
* Git initialized
* Development tools installed
* Node.js
* Rust
* pnpm
* Visual Studio Code

---

# Technology Stack

Frontend

* React
* TypeScript
* Vite

Desktop

* Tauri v2

Styling

* Tailwind CSS
* shadcn/ui

Icons

* Lucide React

Animation

* Framer Motion

State Management

* Zustand

Routing

* Routing (placeholder implementation; final routing architecture will be defined in Phase 03)

---

# Architecture

         Desktop Companion
         (Living Orb · Glass Prompt)
                     │
                     ▼
              Context Engine
          (workspace awareness)
                     │
              ContextSnapshot
                     │
                     ▼
          Conversation Service ──── RetrievalQuery ────► Retrieval Broker
                     │                                (Local File · OneDrive)
                     ▼
              LLM Provider


The Desktop Companion is the interaction surface.

The Context Engine enriches each request with a ContextSnapshot before it reaches the Conversation Service. The Conversation Service receives the snapshot as an input; it does not call the Context Engine directly.

The Conversation Service calls the Retrieval Broker when a request requires document retrieval. The Retrieval Broker fans the query across active connectors and returns a ranked result set. The Conversation Service incorporates those results into its response.

The Workspace sits alongside this flow, providing an expanded view when the interaction outgrows the Glass Prompt.

---

# Context Engine

The Context Engine is the layer responsible for understanding what the user is currently working on.

It sits between the Desktop Companion and the Conversation Service. Before a user's request reaches the conversation pipeline, the Context Engine enriches it with signals derived from the active workspace.

## Signals (Version 1)

- Active project folder
- Recently opened documents
- Current file context passed explicitly by the user

## Responsibilities

- Maintain a lightweight representation of the current workspace context
- Attach relevant context signals to outbound conversation requests
- Expose a clean interface that the Conversation Service depends on without knowing where context comes from

## Interface

The Context Engine exposes a single method and returns a `ContextSnapshot`:

```typescript
interface ContextEngine {
  getSnapshot(): Promise<ContextSnapshot>;
}

interface ContextSnapshot {
  activeProjectFolder: string | null;
  recentDocuments: string[];
  explicitContext: string | null;
}
```

`ContextSnapshot` is the primary contract between the Context Engine and the Conversation Service. Fields not yet populated return `null` or an empty array. The Conversation Service attaches the snapshot to each outbound request.

## Implementation Note

The Context Engine does not perform retrieval. It gathers ambient workspace signals and passes them forward. Retrieval is the Retrieval Broker's responsibility.

In Phase 00, the Context Engine is scaffolded but not connected to live signals. It returns empty context. Actual signal collection begins in a later phase.

---

# Retrieval Broker

The Retrieval Broker is the single interface through which the application retrieves knowledge from external sources.

It decouples the Conversation Service from the implementation details of individual storage systems. Adding a new connector in a future phase does not require changes to the Conversation Service.

## Architecture

```text
Conversation Service
        │
Retrieval Broker
        │
   ┌────┴────┐
   │         │
Local File   OneDrive
Connector    Connector
```

## Version 1 Connectors

**Local File Connector**

Searches indexed content from the user's local file system. Results come from the local vector index (Qdrant) built during the indexing pipeline.

**OneDrive Connector**

Retrieves documents from the user's OneDrive. Searches across personal files accessible via the user's authenticated session.

## Responsibilities

- Accept a structured retrieval query from the Conversation Service
- Fan the query across active connectors
- Rank and merge results into a unified response
- Return a ranked list of document fragments with source metadata

## Interface

The Retrieval Broker exposes a single method. The Conversation Service calls it with a `RetrievalQuery` and receives a `RetrievalResult`:

```typescript
interface RetrievalBroker {
  retrieve(query: RetrievalQuery): Promise<RetrievalResult>;
}

interface RetrievalQuery {
  text: string;
  projectFolder: string | null;
  maxResults: number;
}

interface RetrievalResult {
  fragments: DocumentFragment[];
}

interface DocumentFragment {
  content: string;
  sourcePath: string;
  sourceType: "local" | "onedrive";
  score: number;
}
```

`RetrievalQuery` is the primary contract between the Conversation Service and the Retrieval Broker. Connectors added in future phases receive the same query type. `DocumentFragment.score` is normalized to `[0, 1]` by each connector before the broker merges results.

## Implementation Note

In Phase 00, the Retrieval Broker is not connected to live connectors. Both connectors return empty results. The interface is defined so that Phase 01 can activate connectors without changing the Conversation Service.

---

# Project Knowledge Layer

The Project Knowledge Layer is a conceptual architectural concern rather than a standalone service.

It represents the accumulated understanding the companion develops about a specific project over time: goals, decisions, key documents, recurring entities, and historical conversation context.

## What It Is

- A structured store of project-level knowledge separate from the raw document index
- The source of long-term context that supplements the active workspace signals provided by the Context Engine
- The mechanism through which the companion becomes more useful the longer a user works within a project

## What It Is Not

- A file system
- A chat history store
- A replacement for the vector index

## Relationship to Other Layers

The Project Knowledge Layer is populated by the indexing pipeline and conversation processing. It is queried by the Context Engine when enriching requests with project-level context. It is read-only from the companion's perspective during a conversation.

## Core Types

The following minimal types are defined now so that services built in Phase 01 can reference them without redesign when Project Knowledge is implemented.

```typescript
interface Project {
  id: string;           // UUID
  name: string;
  folderPath: string;
  createdAt: string;    // ISO 8601
}

interface ProjectKnowledgeRepository {
  findByFolderPath(folderPath: string): Promise<Project | null>;
}
```

`Project` is the entity that other services use when they reference "the active project." The `id` field is the stable identifier; `folderPath` is how the Context Engine resolves a project from a file system signal.

`ProjectKnowledgeRepository` is not implemented in Phase 00. It is defined here so that the Context Engine and Conversation Service can declare a dependency on it without knowing its implementation. In Phase 00, a `NullProjectKnowledgeRepository` returns `null` for all queries.

## Implementation Note

The Project Knowledge Layer is not implemented in Phase 00. This section documents the concept and establishes the minimal interface contracts so that architectural decisions made during Phase 00 do not foreclose its introduction in later phases.

---

# Non-Goals

The following features are intentionally excluded from this phase:

* Real AI providers
* IPC communication
* SQLite
* Neo4j
* Qdrant
* OCR
* Search
* RAG
* Memory
* Plugins
* Automation

These are implemented in later phases.

---

# User Flow

```text
Launch Application

↓

Desktop Companion appears (Living Orb)

↓

User enters prompt via Glass Prompt

↓

Context Engine enriches the request

↓

Retrieval Broker surfaces relevant documents

↓

Response displayed inline

↓

User explores navigation or opens Workspace
```

---

## User Flow — Document Recognized

```text
User opens a document

↓

Context Engine detects active file

↓

Companion surfaces a suggestion card in the Glass Prompt

↓

User accepts or dismisses

↓

Accepted: companion summarizes the document in context
```

---

## User Flow — Unified Search

```text
User enters a search query in the Glass Prompt

↓

Retrieval Broker queries Local File Connector and OneDrive Connector

↓

Results ranked and merged

↓

Unified response displayed with source attribution

↓

User selects a result to open or continue in Workspace
```

---

## User Flow — Conversation Grows to Workspace

```text
User opens Glass Prompt

↓

Conversation becomes lengthy

↓

Companion recommends opening Workspace

↓

User accepts

↓

Workspace opens with full conversation history intact

↓

Conversation continues without interruption
```

---

# Confidence Model

The Confidence Model defines how the companion communicates uncertainty to the user.

## Principle

The companion must never present fabricated or unverified content as fact. When the companion is uncertain about retrieved information, the degree of confidence should be reflected in how the response is framed.

## Confidence Levels

**High confidence** — Retrieved from an indexed source with a strong semantic match. The response may reference the source directly.

**Moderate confidence** — Inferred from partial context or a weaker match. The response acknowledges that the information may be incomplete.

**Low confidence** — Generated without retrieved grounding. The response is clearly framed as the model's best attempt without document support.

## Presentation Principle

The companion should make confidence levels visible in a way that is informative but not disruptive. A source attribution, a hedging phrase, or a confidence indicator are all acceptable approaches. The specific presentation mechanism is defined during implementation.

## Implementation Note

The Confidence Model is a product principle in Phase 00. It does not require implementation during this phase. The Conversation Service and Retrieval Broker should be designed in a way that makes confidence metadata available when those components are implemented in later phases.

---

# User Interface Requirements

The Desktop Companion should always remain the primary focus.

Users should never feel lost after launching the application.

Important principles:

* Minimal interface
* Large conversation area
* Fast interactions
* Clean typography
* Consistent spacing
* Accessible controls

---

# Completion Criteria

This phase is complete when:

* The application launches successfully.
* The Living Orb initializes successfully.
* The Glass Prompt opens correctly.
* Users can type messages.
* Mock responses are displayed.
* The interface is responsive.
* Navigation placeholders are accessible.
* Themes function correctly.
* The application feels polished despite having no backend functionality.

---

# Success Definition

A user launching the Enterprise AI Companion for the first time should immediately understand that the application is a desktop-native AI companion — not a chat window they navigate to, but a persistent and accessible presence that understands their work.

Even without AI functionality, the experience should communicate the product's vision through a polished, responsive, and intuitive interface. The architecture introduced in this phase should support the Context Engine, Retrieval Broker, and Project Knowledge Layer without requiring significant redesign when those capabilities are introduced.

---

# Epic 0.1 – Project Foundation

Establish the repository, development environment, and tooling required by all subsequent phases.

## Objectives

* Repository initialized.
* Development environment configured.
* Folder structure established.
* Tooling installed.
* Coding standards configured.
* Version control ready.
* Documentation structure in place.

## Development Environment

Desktop Framework

* Tauri

Frontend

* React
* TypeScript
* Vite

Backend

* Python

Package Management

* pnpm (frontend)
* uv or pip (backend)

Version Control

* Git

## Repository Structure

```text
Enterprise-AI-Companion/
│
├── .claude/
├── .github/
│   └── workflows/
│
├── apps/
│   ├── desktop/
│   └── backend/
│
├── packages/
│
├── database/
│
├── assets/
│
├── docs/
│
├── tests/
│
├── scripts/
│
├── .gitignore
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## Development Tooling

Formatting

* Prettier (frontend)
* Black (backend)

Linting

* ESLint (frontend)
* Ruff (backend)

Type Checking

* TypeScript (frontend)
* mypy (backend)

## Deliverables

* Configured repository
* Standard directory structure
* Development tooling
* Formatting and linting configuration
* Documentation structure
* Version control configuration

## Completion Criteria

* Repository structure matches the architectural specification.
* Development environment builds successfully.
* Frontend dependencies install correctly.
* Formatting tools execute without errors.
* Linters execute successfully.

## Related Documentation

* `docs/architecture/repository-layout.md`
* `docs/architecture/technology-stack.md`
* `docs/decisions/ADR-004-Capability-Based-Architecture.md`

---

# Epic 0.2 – Frontend Foundation

Establish the desktop application and frontend architecture, including the IPC client, routing, state management, and reusable component library.

## Objectives

* Desktop application shell.
* Global layout.
* Navigation system.
* Routing.
* State management.
* Theme management.
* IPC communication layer.
* Notification system.
* Reusable UI component library.
* Responsive desktop interface.

## Frontend Architecture

```text
apps/desktop/
│
├── src/
│   ├── app/
│   ├── components/
│   ├── layouts/
│   ├── pages/
│   ├── routes/
│   ├── services/
│   ├── hooks/
│   ├── stores/
│   ├── styles/
│   ├── types/
│   ├── utils/
│   └── main.tsx
```

## Core Components

Application Shell

* Application initialization
* Window layout
* Global providers
* Theme loading
* Route initialization

Navigation

* Sidebar navigation
* Active page highlighting
* Future extensibility for plugins

Routing

* Page registration
* Error pages
* Lazy loading support

State Management

* Application settings
* User preferences
* Notifications
* Theme

Theme Management

* Light mode
* Dark mode
* System theme detection
* Persistent user preference

IPC Client

* Sending commands
* Receiving responses
* Error translation
* Timeout handling

Reusable UI Components

* Buttons, Forms, Inputs, Dialogs
* Tables, Cards, Navigation components
* Loading indicators, Progress bars
* Empty states, Error states

## Deliverables

* Desktop application shell
* Routing system
* Navigation framework
* Theme management
* State management
* IPC client
* Notification system
* Reusable component library
* Responsive layouts

## Related Documentation

* `docs/architecture/application-layers.md`
* `docs/decisions/ADR-007-IPC-Communication.md`

---

# Epic 0.3 – Application Shell

Create the overall application layout that hosts the Character Widget and all future capability views.

## Components

* Sidebar
* Main content area
* Character Widget panel
* Top navigation
* Status area

The application should feel complete even though functionality has not yet been implemented.

## Sidebar Navigation Placeholders

Sections:

* Home
* Chat
* Workspace
* Search
* Knowledge Graph
* Automation
* Settings

Navigation targets may display placeholder pages at this stage.

## Window Management

* Window resizing
* Minimum dimensions
* Responsive layouts
* Keyboard shortcuts
* Native desktop behavior

## Deliverables

* Application shell with sidebar
* Placeholder navigation pages
* Responsive window management

---

# Epic 0.4 – Character Widget

Build the primary assistant interface.

## Widget Components

* Assistant avatar
* Assistant name
* Online status
* Conversation area
* Prompt input
* Send button
* Attachment button
* Quick action buttons

## Conversation Interface

Implement:

* User messages
* Assistant messages
* Markdown rendering
* Code block rendering
* Timestamp display
* Auto scrolling
* Message animations

Conversation history may remain in memory during this phase.

## Prompt Input

The input area should support:

* Multi-line text
* Enter to send
* Shift + Enter for new line
* Character counter
* Attachment placeholder
* Keyboard shortcuts

The input should feel responsive and polished.

## Animations

Provide subtle animations for:

* Window loading
* Messages
* Sidebar
* Widget expansion
* Buttons
* Hover effects

Animations should improve usability without reducing responsiveness.

## Deliverables

* Character Widget
* Chat interface
* Prompt input
* Message animations

---

# Epic 0.5 – Conversation Architecture

Establish the clean architecture service layer that separates UI from business logic and AI provider communication.

## Architecture

```text
React Hook (thin bridge)
        │
ConversationService (framework-independent)
        │
LLMProvider interface
        │
MockProvider / APIMProvider
```

## LLMProvider Interface

```text
generateResponse(prompt, options?) → Promise<string>
streamResponse(prompt, options?) → AsyncIterable<LLMStreamChunk>
cancel() → void
```

## MockProvider

* Keyword-based response matching
* Simulated typing delay
* Character streaming
* No external dependencies

## APIMProvider

* Native Fetch API only — no vendor SDKs
* Azure API Management gateway
* AbortSignal cooperative cancellation
* Production skeleton with TODO markers for Phase 01

## ConversationService

* Framework-independent class
* Owns AbortController lifecycle
* Communicates via ConversationCallbacks inversion pattern
* No React, Zustand, or DOM APIs

## Dependency Injection

* ConversationServiceContext (React Context)
* ConversationServiceProvider (wraps app tree)
* createLLMProvider factory function
* LLM_CONFIG drives provider selection (mock | apim)

## LLM Configuration

```text
LLMProviderKey: "mock" | "apim"

LLM_CONFIG.provider = "mock"   ← development default
LLM_CONFIG.provider = "apim"   ← production
```

## Deliverables

* LLMProvider interface
* MockProvider
* APIMProvider skeleton
* ConversationService
* ConversationServiceContext + Provider
* createLLMProvider factory
* useConversation hook (thin bridge)
* Zustand conversationStore

---

# Epic 0.6 – Product Identity & Desktop Companion Presence

Define and implement the Desktop Companion's visual identity, interaction model, and desktop presence.

The Living Orb and Glass Prompt form the application's primary interaction surface.

Rather than requiring users to launch and navigate a traditional application window, the Desktop Companion remains immediately accessible through a persistent desktop presence while the Workspace provides an expanded environment for longer interactions.

The objective of this phase is not to build intelligence, but to build the experience.

> **Implementation Note**
>
> Earlier epics refer to the "Character Widget." As the product vision evolved, this concept became the Living Orb and Glass Prompt interaction model. References to the Character Widget in earlier epics should be interpreted accordingly.

**Status:** Complete

---

## 0.6.1 Product Requirements Document (PRD)

### Overview

This Product Requirements Document defines the vision, goals, user experience, and functional requirements for the Product Identity & Desktop Companion Presence epic.

Unlike traditional AI chat applications that require users to open a dedicated window before interacting, Enterprise AI Companion introduces a persistent desktop-native companion that is immediately accessible from anywhere within Windows. The companion understands what the user is working on, can retrieve knowledge from local and cloud sources, and accumulates project context over time.

This epic establishes the Desktop Companion as the primary interface of the application while positioning the full Workspace as a secondary interface for extended interactions.

The objective is to create an experience where interacting with AI feels instantaneous, natural, and integrated into the desktop environment — not confined to a standalone application window, and not requiring the user to explain their context on every interaction.

---

## Vision

Enterprise AI Companion should feel less like a chat application and more like a native desktop companion that understands the user's work.

The companion should always be available without interrupting the user's workflow.

Rather than requiring users to launch an application and navigate to a conversation window, the companion remains present as a lightweight floating presence capable of handling quick interactions while providing seamless access to the complete workspace whenever deeper interaction is required.

The companion knows what the user is working on. It can retrieve documents from local storage and cloud drives. It accumulates knowledge about active projects. Over time, it becomes more useful without requiring the user to teach it anything explicitly.

The Desktop Companion should become the product's defining experience and primary interaction model.

---

## Problem Statement

Current AI desktop applications generally follow the same interaction pattern:

Application
→ Chat Window
→ AI Response

This introduces unnecessary friction for simple interactions.

Users must:

- Locate the application.
- Open the application.
- Navigate to the chat interface.
- Re-establish context for every new request.
- Begin interacting.

For frequent AI usage, these repeated actions interrupt workflow and reduce accessibility. The need to re-state context on every interaction compounds the friction further.

Enterprise AI Companion aims to eliminate this friction by making AI continuously available through a persistent desktop companion that already understands the user's work.

---

## Goals

The Product Identity & Desktop Companion Presence epic aims to achieve the following goals:

- Establish the Desktop Companion as the primary interaction point.
- Provide instant access to AI from anywhere on the desktop.
- Reduce interaction friction for common AI tasks.
- Create a unique visual identity distinct from existing AI tools.
- Maintain a Windows-native user experience.
- Support smooth transitions between lightweight interactions and the full Workspace.
- Introduce the Context Engine architecture so workspace signals can enrich requests.
- Introduce the Retrieval Broker architecture so knowledge retrieval is connector-agnostic.
- Create a scalable architecture capable of supporting the Project Knowledge Layer in later phases.

---

## Non-Goals

The following features are intentionally excluded from this version of the product:

- Voice conversations
- Wake-word detection
- Autonomous desktop monitoring
- Automatic task execution
- Clipboard intelligence
- File monitoring
- Download detection
- Email analysis
- Calendar awareness
- Screen understanding

These capabilities may be introduced in future releases once the companion foundation has matured.

---

# Target Users

Primary users include:

- Software engineers
- Students
- Researchers
- Technical professionals
- Enterprise users

These users frequently interact with AI throughout the day and benefit from minimizing context switching.

---

# User Experience Principles

The Desktop Companion should follow these core design principles. See also: Experience Principles in the Phase 00 overview for the full principle set.

## Always Available

The Desktop Companion should remain accessible regardless of which application the user is currently using.

---

## Minimal Friction

Simple requests should require as few interactions as possible.

Opening the Glass Prompt should feel nearly instantaneous.

---

## Progressive Disclosure

Quick interactions should remain lightweight.

More complex workflows should naturally transition into the Workspace without interrupting the conversation.

---

## Windows Native

The application should respect Windows interaction patterns, keyboard shortcuts, visual language, and window behavior.

The product should not imitate macOS conventions.

---

## Calm Presence

The Desktop Companion should feel alive without becoming distracting.

Animations should communicate state rather than seek attention.

---

# User Interaction Flows

## Quick Question

User
↓

Clicks the Living Orb

↓

Glass Prompt opens

↓

User asks a question

↓

Companion responds inline

↓

Glass Prompt closes automatically

---

## Extended Conversation

User
↓

Opens Glass Prompt

↓

Conversation becomes lengthy

↓

Companion recommends opening Workspace

↓

Workspace opens

↓

Conversation continues without interruption

---

## Keyboard Workflow

User presses

Ctrl + K

↓

Glass Prompt opens immediately

↓

Prompt receives keyboard focus

↓

User interacts entirely using the keyboard

---

# Functional Requirements

## Living Orb

The Living Orb shall:

- Remain visible on the desktop.
- Support dragging and repositioning.
- Persist its position between sessions.
- Display multiple interaction states.
- Support multi-monitor environments.
- Remain lightweight during idle operation.

---

## Glass Prompt

The Glass Prompt shall:

- Open instantly.
- Automatically focus the input field.
- Support keyboard-first interaction.
- Display streamed AI responses.
- Support markdown rendering.
- Close gracefully.
- Preserve unfinished conversations.

---

## Workspace Transition

The application shall:

- Preserve conversation context.
- Open the workspace without resetting state.
- Continue streaming responses during transition.
- Allow users to return to lightweight interactions.

---

## Living Orb States

The Living Orb shall visually represent:

- Initializing
- Idle
- Hover
- Active
- Processing
- Streaming
- Success
- Notification
- Sleeping
- Error

Each state should have a distinct animation while maintaining a consistent visual identity.

---

## Accessibility

The Desktop Companion shall:

- Support keyboard navigation.
- Support screen readers where applicable.
- Respect reduced motion preferences.
- Maintain sufficient visual contrast.
- Provide accessible focus indicators.

---

# Non-Functional Requirements

Performance objectives include:

- Launch time below 2 seconds.
- Glass Prompt opens within 150 milliseconds.
- Smooth 60 FPS animations.
- Minimal idle CPU usage.
- Low idle memory consumption.
- GPU-accelerated animations where supported.

---

# Success Criteria

The epic is considered successful when:

- Users can interact with AI without opening the Workspace.
- Desktop interactions feel responsive.
- Workspace transitions are seamless.
- The Desktop Companion has a distinct and recognizable visual identity.
- The overall experience feels native to Windows.
- Existing conversation functionality continues to operate correctly.

---

# Risks

Potential implementation risks include:

- Desktop overlays conflicting with Windows behavior.
- Animation performance on lower-end hardware.
- Window focus management.
- Multi-monitor positioning.
- Future desktop integration introducing architectural complexity.

These risks should be addressed during technical design.

---

# Dependencies

This epic depends on:

- Epic 0.1 – Project Foundation
- Epic 0.2 – Frontend Foundation
- Epic 0.3 – Application Shell
- Epic 0.4 – Character Widget
- Epic 0.5 – Conversation Architecture

---

# Deliverables

Completion of this epic should produce:

- Living Orb
- Glass Prompt
- Desktop Presence Layer
- Workspace Transition Flow
- Desktop Companion State System
- `ContextEngine` interface with `ContextSnapshot` type (scaffolded)
- `RetrievalBroker` interface with `RetrievalQuery` and `RetrievalResult` types (scaffolded, two connectors defined)
- `Project` entity and `ProjectKnowledgeRepository` interface stub
- Windows-native interaction model

---

## Epic 0.6.2 – Technical Design Document (TDD)

### Overview

This Technical Design Document defines the software architecture required to implement the Product Identity & Desktop Companion Presence epic.

The objective is to establish a modular, maintainable, and extensible architecture that enables the Desktop Companion to exist as a persistent presence on the user's desktop while remaining decoupled from AI providers, business logic, and future desktop intelligence features.

The architecture introduced in this document serves as the foundation for future capabilities such as desktop awareness, notifications, contextual actions, and proactive assistance without requiring significant redesign.

---

# Design Principles

The implementation follows the following engineering principles.

## Separation of Concerns

Each component should have a single responsibility.

The Living Orb should never directly communicate with AI providers.

Business logic should remain independent of UI components.

---

## Modular Architecture

Every major subsystem should be replaceable without affecting unrelated components.

Examples include:

- AI Provider
- Desktop Presence
- Window Management
- Overlay Rendering
- Conversation Service

---

## Event-Driven Communication

Components should communicate through events and well-defined interfaces rather than directly manipulating each other.

This minimizes coupling and simplifies future feature additions.

---

## Windows-First Design

The implementation should prioritize native Windows behavior.

Window management, shortcuts, overlays, acrylic effects, and interaction patterns should follow Windows conventions.

---

## Future Extensibility

The architecture should support future capabilities including:

- Voice interaction
- Desktop intelligence
- File awareness
- Clipboard monitoring
- Notification framework
- Plugin integration

without requiring major architectural changes.

---

# High-Level Architecture

The Desktop Companion layer is positioned above the existing conversation architecture. The Context Engine enriches requests before they reach the Conversation Service. The Retrieval Broker is called by the Conversation Service when document retrieval is required.

```

Desktop Companion
(Living Orb · Glass Prompt)

↓

Desktop Presence Layer

↓

Context Engine
(produces ContextSnapshot)

↓ ContextSnapshot

Conversation Service ──── RetrievalQuery ────► Retrieval Broker
                                              (Local File · OneDrive)
↓

LLM Provider

↓

Azure API Management

↓

LLM

```

The Living Orb is responsible only for user interaction. It has no knowledge of AI providers, conversations, or retrieval.

The Context Engine produces a ContextSnapshot and passes it to the Conversation Service. The Conversation Service receives context as an input; it does not call the Context Engine.

The Conversation Service calls the Retrieval Broker when a request requires document retrieval. The Retrieval Broker resolves the query across connectors and returns a ranked result set. The Conversation Service depends on the Retrieval Broker interface, not on any individual connector.

---

# Component Responsibilities

## Living Orb

Responsible for:

- Visual representation
- Mouse interaction
- Dragging
- Hover animations
- State visualization
- Opening the Glass Prompt

The Living Orb should not:

- Manage conversations
- Call APIs
- Store messages
- Execute business logic

---

## Glass Prompt

Responsible for:

- Prompt input
- Streaming responses
- Markdown rendering
- Conversation preview
- Keyboard interaction

The Glass Prompt delegates all AI interactions to the Conversation Service.

---

## Desktop Presence Layer

Acts as the orchestration layer between desktop UI components and backend services.

Responsibilities include:

- Overlay management
- Window coordination
- Desktop positioning
- Future desktop event integration

---

## Conversation Service

Responsible for:

- Message lifecycle
- Conversation state
- Streaming orchestration
- Accepting a `ContextSnapshot` as an input to each request
- Calling the Retrieval Broker with a `RetrievalQuery` when document retrieval is required
- Incorporating retrieved `DocumentFragment` results into the outbound request

Conversation Service remains UI-independent. It receives a `ContextSnapshot` from its caller; it does not call the Context Engine directly. It calls the Retrieval Broker by interface; it has no knowledge of individual connectors.

---

## LLM Provider

Responsible for:

- Request execution
- Response streaming
- Provider abstraction
- Error normalization

The provider communicates exclusively through Azure API Management.

---

## Context Engine

Responsible for:

- Observing active workspace signals (open documents, active project folder)
- Constructing a lightweight context snapshot for each request
- Passing context to the Conversation Service without exposing workspace implementation details

The Context Engine does not perform retrieval. It gathers ambient signals and packages them.

In Phase 00, the Context Engine returns empty context. The interface is defined so that later phases can attach real workspace signals without changing the Conversation Service.

---

## Retrieval Broker

Responsible for:

- Accepting structured retrieval queries from the Conversation Service
- Routing queries to active connectors
- Ranking and merging results across connectors
- Returning a unified, attributed result set

The Retrieval Broker owns the connector lifecycle. The Conversation Service depends on the broker interface only.

**Version 1 Connectors:**

- Local File Connector — queries the local vector index (Qdrant)
- OneDrive Connector — queries the user's authenticated OneDrive

In Phase 00, both connectors are scaffolded but inactive. They return empty results.

---

# Proposed Services

The following services are introduced by this epic.

## DesktopPresenceService

Coordinates all desktop presence functionality.

Responsibilities:

- Orb lifecycle
- Overlay lifecycle
- Desktop visibility
- Future desktop integrations

---

## OverlayManager

Manages lightweight overlay windows.

Responsibilities:

- Glass Prompt
- Notifications
- Future contextual overlays

---

## WindowManager

Coordinates transitions between:

- Orb
- Glass Prompt
- Workspace

Responsible for maintaining application state across windows.

---

## OrbController

Controls the Living Orb.

Responsibilities:

- Interaction handling
- State updates
- Animation requests

Business logic remains outside this controller.

---

## ContextEngine

Constructs workspace context snapshots.

Responsibilities:

- Observe active workspace signals
- Produce a ContextSnapshot consumed by the Conversation Service
- Expose a clean interface independent of how signals are collected

---

## RetrievalBroker

Resolves retrieval queries across connectors.

Responsibilities:

- Manage connector registry
- Fan queries across active connectors
- Merge and rank results
- Return attributed document fragments

---

## OrbStateMachine

Defines every possible state of the Living Orb.

The state machine prevents invalid transitions and ensures consistent animations.

Supported states include:

- Initializing
- Idle
- Hover
- Listening
- Processing
- Streaming
- Success
- Notification
- Sleeping
- Error

---

## AnimationController

Responsible for:

- Animation timing
- Motion transitions
- Animation interruption
- State synchronization

Animations should be entirely data-driven.

---

# Component Hierarchy

DesktopOverlay

├── LivingOrb

├── GlassPrompt

├── NotificationOverlay

└── AnimationLayer

Each component should remain independently testable.

---

# Window Flow

Quick Interaction

Living Orb

↓

Glass Prompt

↓

Conversation Service

↓

Inline Response

---

Extended Interaction

Living Orb

↓

Glass Prompt

↓

Conversation exceeds lightweight interaction

↓

Workspace opens

↓

Conversation continues

No conversation state should be lost during this transition.

---

# State Management

UI State

Managed by Zustand.

Conversation State

Managed by Conversation Service.

Provider State

Managed by LLM Provider.

Desktop State

Managed by DesktopPresenceService.

These state domains should remain independent.

---

# Error Handling

Failures should degrade gracefully.

Examples:

LLM unavailable

↓

Living Orb transitions to Error state

↓

Allow retry

↓

Maintain conversation history

Desktop overlays should never crash because an AI request fails.

---

# Performance Considerations

The implementation should prioritize:

- Fast startup
- Low idle memory
- Minimal CPU usage
- GPU accelerated animations
- Lazy initialization
- Window reuse

Heavy services should initialize only when required.

---

# Security Considerations

The desktop layer should never directly expose:

- API keys
- Authentication tokens
- Provider credentials

All AI communication continues through Azure API Management.

Sensitive configuration remains isolated from UI components.

---

# Dependencies

This epic depends on:

- Epic 0.1 – Project Foundation
- Epic 0.2 – Frontend Foundation
- Epic 0.3 – Application Shell
- Epic 0.4 – Character Widget
- Epic 0.5 – Conversation Architecture

---

# Deliverables

Completion of this technical design introduces:

- DesktopPresenceService
- OverlayManager
- WindowManager
- OrbController
- OrbStateMachine
- AnimationController
- `ContextEngine` interface with `ContextSnapshot` type
- `RetrievalBroker` interface with `RetrievalQuery`, `RetrievalResult`, and `DocumentFragment` types
- `LocalFileConnector` and `OneDriveConnector` stubs
- `Project` entity and `ProjectKnowledgeRepository` interface stub
- Updated application architecture
- Window transition framework
- Event-driven desktop interaction model

---

# Out of Scope

The following are intentionally excluded from this epic:

- Voice assistant
- Desktop automation
- Clipboard monitoring
- Download detection
- Email awareness
- Calendar integration
- Screen understanding
- Autonomous AI actions

These capabilities will build upon this architecture in future phases.

---

## Epic 0.6.3 – Visual Design Language

### Overview

This document defines the visual identity, motion principles, interaction language, and aesthetic guidelines for Enterprise AI Companion.

The objective is to establish a distinctive, professional, and cohesive visual language that reflects the Desktop Companion's role as a persistent presence in the user's environment while remaining consistent with Windows design principles.

The Desktop Companion should feel calm, intelligent, and trustworthy rather than flashy or distracting.

---

# Design Philosophy

Enterprise AI Companion should not resemble a traditional chat application.

Instead, it should feel like a native part of the user's desktop environment.

Every visual element should communicate purpose.

Animations should communicate system state.

Colors should communicate hierarchy.

Motion should communicate interaction.

The interface should never use visual effects purely for decoration.

---

# Design Principles

## Calm Presence

The Desktop Companion should always feel available without demanding attention.

It should exist quietly until needed.

---

## Functional Beauty

Every visual effect must have a purpose.

Blur should improve focus.

Motion should indicate transitions.

Glow should represent activity.

Nothing should exist solely for decoration.

---

## Windows Native

The application should embrace Windows design language.

It should feel at home alongside modern Windows applications rather than imitating another operating system.

---

## Consistency

Every interaction should follow predictable patterns.

Buttons, overlays, animations, spacing, and typography should behave consistently throughout the application.

---

# Visual Identity

The visual identity consists of four primary elements.

• Living Orb

• Glass Prompt

• Workspace

• Supporting Overlays

Each should appear as part of the same design system.

---

# Living Orb

The Living Orb is the primary visual identity of Enterprise AI Companion.

It should immediately communicate:

- Availability
- Intelligence
- Calmness
- Responsiveness

The orb should never appear static.

Subtle movement should indicate that the Desktop Companion is active.

The orb should avoid appearing cartoonish or overly futuristic.

---

## Orb States

The Living Orb should visually represent:

- Initializing
- Idle
- Hover
- Active
- Listening
- Processing
- Streaming
- Success
- Notification
- Sleeping
- Error

Each state should be recognizable while maintaining the same overall identity.

---

# Glass Prompt

The Glass Prompt serves as the primary interaction surface.

Its visual goals are:

- Lightweight
- Fast
- Minimal
- Focused

The prompt should appear to emerge naturally from the Living Orb rather than opening as a separate application.

---

# Workspace

The Workspace is intended for extended interactions.

Unlike the Glass Prompt, the Workspace prioritizes information density while maintaining the same design language.

The transition between the two should feel continuous.

---

# Motion Language

Animations should always communicate intent.

Animation categories include:

## Presence

Small idle movement indicating availability.

---

## Transition

Opening and closing overlays.

---

## Feedback

Button presses.

Hover effects.

Loading indicators.

---

## State Change

Orb state transitions.

Conversation streaming.

Notification appearance.

---

# Animation Principles

Animations should be:

- Smooth
- Consistent
- Purposeful
- Interruptible

Avoid excessive bounce or exaggerated motion.

The interface should feel professional rather than playful.

---

# Color Philosophy

Colors should emphasize clarity.

Primary colors indicate interaction.

Secondary colors support hierarchy.

Accent colors indicate state changes.

Error and warning colors should follow Windows accessibility guidelines.

---

# Material System

The application should use modern Windows materials where appropriate.

Preferred materials include:

- Acrylic
- Mica
- Transparent overlays
- Soft shadows
- Layered elevation

Materials should enhance usability rather than distract from content.

---

# Typography

Typography should prioritize readability.

Headings establish hierarchy.

Body text remains highly legible.

Monospaced fonts are reserved for code and technical content.

Typography should remain consistent across overlays and workspace views.

---

# Iconography

Icons should be:

- Minimal
- Consistent
- Recognizable
- Line-based

Icons should communicate meaning without requiring labels whenever possible.

---

# Spacing System

The interface should use a consistent spacing scale.

Whitespace should improve readability and reduce visual clutter.

Components should never appear crowded.

---

# Window Behavior

Overlay windows should:

- Open smoothly.
- Respect screen boundaries.
- Support multiple monitors.
- Maintain visual continuity.

Transitions between overlays and the Workspace should feel seamless.

---

# Accessibility

Visual design should support:

- High contrast modes
- Reduced motion preferences
- Keyboard navigation
- Clear focus indicators
- Readable typography

Accessibility should be considered a core design requirement rather than an optional enhancement.

---

# Brand Personality

Enterprise AI Companion should feel:

- Intelligent
- Calm
- Reliable
- Professional
- Helpful
- Modern

It should avoid appearing:

- Cartoonish
- Overly animated
- Aggressive
- Distracting
- Childish
- Gamified

---

# Design Consistency Rules

Every new interface introduced into the application should follow this design language.

No component should introduce a conflicting visual style without updating this document.

This document serves as the visual reference for all future UI development.

---

# Deliverables

Completion of this document establishes:

- Living Orb visual identity
- Motion language
- Glass Prompt styling
- Workspace styling
- Material system
- Typography guidelines
- Accessibility guidelines
- Brand personality
- UI consistency rules

---

## Epic 0.6.4 – Implementation Plan

### Overview

This Implementation Plan defines the engineering roadmap for completing the Product Identity & Desktop Companion Presence epic.

The objective is to deliver the Living Orb, Glass Prompt, Desktop Presence Layer, and supporting infrastructure through incremental, independently testable tasks while minimizing integration risk.

Implementation should proceed in small, well-defined milestones where each task introduces a complete, reviewable piece of functionality.

---

# Implementation Strategy

Development follows an incremental approach.

Each task should:

- Be independently implementable.
- Be independently testable.
- Avoid introducing unnecessary dependencies.
- Preserve application stability.
- Build upon previously completed tasks.

No task should require unfinished functionality from a later task.

---

# Task Breakdown

## Task 0.6.4.1 – Desktop Presence Foundation

### Objective

Introduce the desktop presence architecture without modifying existing application functionality.

### Scope

- DesktopPresenceService
- Overlay infrastructure
- Desktop lifecycle management
- Initial service registration

### Deliverables

- DesktopPresenceService
- Service interfaces
- Basic initialization
- Unit tests

### Dependencies

- Epic 0.5 – Conversation Architecture

---

## Task 0.6.4.2 – Living Orb

### Objective

Implement the persistent Living Orb.

### Scope

- Orb component
- Dragging
- Position persistence
- Hover interaction
- Idle behavior

### Deliverables

- Living Orb
- Position storage
- Interaction events
- Accessibility support

### Dependencies

Task 0.6.4.1

---

## Task 0.6.4.3 – Orb State Machine

### Objective

Implement the Living Orb state machine.

### Scope

Supported states:

- Initializing
- Idle
- Hover
- Active
- Processing
- Streaming
- Success
- Notification
- Sleeping
- Error

### Deliverables

- OrbStateMachine
- State transitions
- Animation bindings

### Dependencies

Task 0.6.4.2

---

## Task 0.6.4.4 – Glass Prompt

### Objective

Implement the lightweight interaction surface.

### Scope

- Acrylic window
- Prompt input
- Keyboard shortcuts
- Streaming output
- Markdown rendering

### Deliverables

- Glass Prompt
- Keyboard interaction
- Prompt lifecycle
- Streaming support

### Dependencies

Task 0.6.4.3

---

## Task 0.6.4.5 – Workspace Transition

### Objective

Implement seamless transitions between lightweight interactions and the full workspace.

### Scope

- Window transition
- Conversation persistence
- Focus management
- Window restoration

### Deliverables

- Transition manager
- Conversation continuity
- Window synchronization

### Dependencies

Task 0.6.4.4

---

## Task 0.6.4.6 – Animation System

### Objective

Implement a unified animation framework.

### Scope

- Motion presets
- Animation controller
- State animations
- Transition animations

### Deliverables

- AnimationController
- Motion library
- Animation utilities

### Dependencies

Task 0.6.4.3

---

## Task 0.6.4.7 – Windows Native Experience

### Objective

Polish the user experience to align with Windows conventions.

### Scope

- Acrylic materials
- Window behavior
- Multi-monitor support
- Keyboard navigation
- Accessibility improvements

### Deliverables

- Windows-native interactions
- UI polish
- Accessibility validation

### Dependencies

Task 0.6.4.5

---

## Task 0.6.4.8 – Integration & Validation

### Objective

Validate the complete Desktop Companion experience.

### Scope

- End-to-end testing
- Performance validation
- Bug fixes
- Regression testing

### Deliverables

- Stable implementation
- Integration report
- Performance metrics
- Updated documentation

### Dependencies

All previous tasks

---

# Development Workflow

Every implementation task follows the same lifecycle.

Planning

↓

Technical Review

↓

Claude Code Implementation

↓

Manual Review

↓

Testing

↓

Documentation Update

↓

Git Commit

↓

Next Task

No task should be considered complete until all stages have been successfully completed.

---

# Testing Strategy

Each implementation task should include:

## Unit Testing

Validate isolated functionality.

---

## Integration Testing

Verify interactions between new and existing systems.

---

## Manual Validation

Confirm expected user experience.

---

## Performance Validation

Measure startup time, animation smoothness, and resource usage.

---

# Documentation Requirements

Each completed task should update:

- Architecture documentation (if required)
- Implementation progress
- Changelog
- Known limitations

Documentation should remain synchronized with implementation.

---

# Risk Management

Potential risks include:

- Overlay window inconsistencies
- Animation performance
- Window focus conflicts
- State synchronization issues
- Cross-monitor behavior

Each risk should be evaluated during implementation and addressed before proceeding to subsequent tasks.

---

# Definition of Done

The Implementation Plan is considered complete when:

- All implementation tasks are completed.
- All deliverables have been validated.
- Performance objectives have been achieved.
- Accessibility requirements have been satisfied.
- Documentation reflects the implemented system.
- The Living Orb is established as the primary interaction entry point for the Desktop Companion.

---

## Epic 0.6.5 – Acceptance Criteria

### Overview

This document defines the measurable conditions required for Epic 0.6 – Product Identity & Desktop Companion Presence to be considered complete.

All acceptance criteria must be satisfied before the epic can be marked as complete and implementation can proceed to the next phase.

---

# Functional Acceptance Criteria

## Living Orb

The Living Orb shall:

- Remain visible throughout the user's desktop session.
- Support mouse interaction.
- Support dragging and repositioning.
- Persist its position between application launches.
- Display all defined interaction states.
- Remain responsive during AI interactions.

---

## Glass Prompt

The Glass Prompt shall:

- Open instantly from the Living Orb.
- Open using the global keyboard shortcut.
- Automatically focus the input field.
- Support streamed AI responses.
- Support Markdown rendering.
- Close without losing conversation state.

---

## Workspace Transition

The application shall:

- Transition smoothly between the Glass Prompt and Workspace.
- Preserve the active conversation.
- Maintain streaming responses during transitions.
- Restore focus correctly.

---

## Desktop Presence

The desktop presence layer shall:

- Initialize correctly during application startup.
- Manage overlay visibility.
- Support multiple monitor configurations.
- Operate independently of AI provider implementations.

---

## Conversation Integration

The Desktop Companion shall:

- Reuse the existing Conversation Service.
- Preserve conversation history.
- Display provider errors gracefully.
- Continue functioning after transient failures.

---

# Visual Acceptance Criteria

The implementation shall satisfy the approved Visual Design Language.

This includes:

- Consistent spacing.
- Consistent typography.
- Consistent animations.
- Windows-native appearance.
- Calm interaction patterns.
- Professional visual identity.

---

# Performance Acceptance Criteria

The implementation shall meet the following performance goals:

- Application startup remains within the defined performance budget.
- Glass Prompt opens with minimal perceived delay.
- Animations remain smooth under normal system load.
- Idle CPU usage remains minimal.
- Idle memory usage remains low.
- No unnecessary background processing occurs.

---

# Accessibility Acceptance Criteria

The Desktop Companion shall:

- Support keyboard-only interaction.
- Respect reduced-motion preferences.
- Provide visible focus indicators.
- Maintain readable contrast.
- Preserve usability across supported display scales.

---

# Architecture Acceptance Criteria

The implementation shall maintain the approved architecture.

Specifically:

- UI components remain independent of AI providers.
- Business logic remains outside presentation components.
- Desktop Presence remains modular.
- Services communicate through defined interfaces.
- No architectural shortcuts are introduced during implementation.

---

# Quality Acceptance Criteria

Before completion:

- All planned implementation work packages are complete.
- Critical defects are resolved.
- No known blocking issues remain.
- Documentation reflects the implemented system.
- Code follows project standards.

---

# Definition of Done

Epic 0.6 is considered complete when:

- All functional requirements have been implemented.
- All acceptance criteria have been satisfied.
- Manual validation confirms the expected user experience.
- Performance targets have been achieved.
- Accessibility requirements have been met.
- The Living Orb is established as the primary interaction entry point for the Desktop Companion.

---

## Epic 0.6.6 – Future Enhancements

### Overview

This section outlines capabilities intentionally excluded from the initial implementation of the Product Identity & Desktop Companion Presence epic.

These enhancements are outside the scope of Version 1 but have been considered during architectural design to minimize future refactoring.

The purpose of this section is to document the long-term vision without increasing the implementation scope of the current epic.

---

# Desktop Intelligence

The Desktop Presence architecture is designed to support future desktop-aware capabilities.

Potential enhancements include:

- Intelligent desktop event monitoring
- Context-aware companion suggestions
- Active application awareness
- Window context detection
- Smart workflow recommendations

These features should be implemented only after the desktop presence foundation has matured.

---

# File Intelligence

Future versions may allow the Desktop Companion to understand and react to files.

Examples include:

- Drag-and-drop file analysis
- Automatic document summarization
- Intelligent file categorization
- Recent file awareness
- Contextual document suggestions

No background file monitoring will be implemented in Version 1.

---

# Clipboard Intelligence

Potential clipboard capabilities include:

- Clipboard history awareness
- Smart paste suggestions
- Code formatting assistance
- Automatic content summarization
- Context-sensitive clipboard actions

Clipboard access should always remain transparent and user-controlled.

---

# Voice Interaction

Future releases may introduce voice capabilities.

Potential features include:

- Push-to-talk interaction
- Continuous voice conversations
- Wake-word detection
- Speech-to-text
- Text-to-speech
- Voice personalization

Voice interaction is intentionally excluded from Version 1.

---

# Notification Framework

The Desktop Companion may eventually support proactive notifications.

Examples include:

- Task reminders
- Workflow suggestions
- Background job completion
- AI-generated recommendations
- Contextual alerts

Notifications should remain non-intrusive and fully configurable.

---

# Desktop Automation

Future automation capabilities may include:

- User-approved desktop actions
- Workflow automation
- Application launching
- File organization
- Productivity shortcuts

All automation should require explicit user control and confirmation where appropriate.

---

# Plugin Ecosystem

The architecture is designed to support a modular plugin system.

Potential plugin categories include:

- Productivity tools
- Development tools
- Enterprise integrations
- Communication platforms
- Knowledge management systems

Plugin support will be introduced in a later project phase.

---

# Enterprise Features

Future enterprise enhancements may include:

- Organization-wide companion configuration
- Enterprise policy enforcement
- Team knowledge sharing
- Advanced auditing
- Administrative controls

These capabilities belong to the Enterprise phase of the roadmap.

---

# AI Enhancements

The provider architecture enables future AI capabilities such as:

- Multi-agent workflows
- Long-term memory
- Personalized companion behavior
- Advanced reasoning pipelines
- Tool calling
- Retrieval-augmented workflows
- Model routing and optimization

These features will build upon the existing LLM Provider architecture.

---

# Design Evolution

The visual identity may continue evolving through:

- Additional animation states
- Seasonal themes
- Custom companion appearances
- User personalization
- Enhanced motion language

Future visual enhancements should preserve the core design principles established in the Visual Design Language.

---

# Guiding Principles

Future enhancements should follow these principles:

- Preserve modular architecture.
- Maintain Windows-native behavior.
- Prioritize performance.
- Respect user privacy.
- Require minimal architectural refactoring.
- Build upon existing services instead of replacing them.

---

# Summary

The implementation delivered by Epic 0.6 establishes the architectural and visual foundation for Enterprise AI Companion.

Future enhancements should extend this foundation incrementally while preserving the product vision of a persistent, intelligent, and professional desktop AI companion.

---

## Phase 00 Completion Checklist

This checklist is the authoritative record of everything required for Phase 00 to be complete. It incorporates the results of the full implementation audit conducted against the current codebase and the post-redesign architecture.

Items marked ✅ are verified complete in the current codebase. Items marked ☐ are open.

Status key: ✅ Complete · ☐ Not done · ⚠️ Needs rework

---

### Foundation

- ✅ Repository initialized with Git and version control configured
- ✅ Development tooling configured (Prettier, ESLint, TypeScript, Husky, lint-staged)
- ✅ pnpm workspace configured
- ✅ Tauri v2 desktop application building successfully
- ✅ React 19 + Vite frontend bootstrapped
- ✅ Tauri application identity updated (`productName`: "Enterprise AI Companion", `identifier`: "com.volvogroup.enterprise-ai-companion", window `title` corrected)
- ✅ Minimum window dimensions set in `tauri.conf.json` (minWidth: 960, minHeight: 640; default 1280×800)
- ☐ Python backend directory scaffolded with README (Phase 01 requires it to exist)
- ☐ Directory layout decision recorded: confirm `frontend/` as permanent home or migrate to `apps/desktop/` per architecture spec

---

### Frontend Foundation

- ✅ AppShell layout with animated collapsible sidebar
- ✅ TopBar and StatusBar
- ✅ Theme management: light / dark / system, localStorage persistence, media-query listener
- ✅ Zustand stores: `conversationStore`, `layoutStore`, `navigationStore`, `orbStore`
- ✅ Navigation via `navigationStore` + `MainContent` page router
- ✅ 7 navigation items with placeholder pages
- ☐ `shadcn/ui` base components generated into `src/components/ui/` (Button, Input, Dialog — required by Glass Prompt)
- ☐ Global keyboard shortcut Ctrl+K wired to open Glass Prompt
- ☐ Notification service scaffolded (stub only)

---

### Conversation Architecture

- ✅ `LLMProvider` interface (`generateResponse`, `streamResponse`, `cancel`)
- ✅ `MockProvider` with keyword responses, 600 ms delay, 18 ms/character streaming
- ✅ `APIMProvider` skeleton (Fetch + SSE structure, `APIMError`, AbortController)
- ✅ `ConversationService` with streaming lifecycle and `ConversationCallbacks` inversion
- ✅ `ConversationServiceContext` + `ConversationServiceProvider`
- ✅ `ProviderFactory` with exhaustive provider switch and `assertNever`
- ✅ `useConversation` hook (thin bridge to Zustand store)
- ✅ `conversationStore` with all message operations
- ✅ `ConversationService.send()` updated to accept optional `context?: ContextSnapshot` (signature seam for Phase 01; `context` is ignored in Phase 00)

---

### Character Widget

- ✅ `AssistantWidget` assembling header, message list, and footer
- ✅ `MessageBubble` with react-markdown, remark-gfm, streaming cursor, copy button
- ✅ `MessageList` with auto-scroll-to-bottom and `TypingIndicator`
- ✅ `PromptInput` auto-resize, Enter to send, Shift+Enter for newline, 4 000-character limit
- ✅ `TypingIndicator` animated three-dot component
- ✅ `QuickActions` prompt chips
- ✅ `SendButton` with streaming cancel state

---

### Architectural Interface Stubs

These interfaces are defined in the architecture document but do not yet exist in the codebase. They must be created before Phase 01 begins.

- ✅ `services/context/ContextEngine.ts` — `ContextEngine` interface + `ContextSnapshot` type
- ✅ `services/context/NullContextEngine.ts` — returns empty `ContextSnapshot` for all fields
- ✅ `services/retrieval/RetrievalBroker.ts` — `RetrievalBroker` interface + `RetrievalQuery`, `RetrievalResult`, `DocumentFragment` types
- ✅ `services/retrieval/NullRetrievalBroker.ts` — returns empty `RetrievalResult`
- ✅ `services/retrieval/connectors/LocalFileConnector.ts` — stub returning empty results
- ✅ `services/retrieval/connectors/OneDriveConnector.ts` — stub returning empty results
- ✅ `services/knowledge/ProjectKnowledgeRepository.ts` — `ProjectKnowledgeRepository` interface + `Project` type
- ✅ `services/knowledge/NullProjectKnowledgeRepository.ts` — returns `null` for `findByFolderPath`
- ✅ Unit tests for all null implementations

---

### Living Orb

- ✅ `LivingOrb` component with CSS state classes, accessibility, and interaction callbacks
- ✅ `OrbContainer` GPU-composited fixed-layer positioning
- ✅ `OrbIcon` glass sphere (linear-gradient base, radial depth overlay, specular highlight)
- ✅ `orbTheme` design tokens
- ✅ `orbStore` with position persistence (localStorage) and viewport clamping
- ✅ `useOrbPosition` and `useOrbDrag` hooks
- ✅ `OrbLayer` wiring: position + drag + OrbController registration + state subscription
- ☐ Multi-monitor orb positioning (monitor boundary detection)

---

### Orb State Machine

- ✅ `OrbStateMachine` deterministic FSM — throws on invalid transition
- ✅ Subscribe / unsubscribe pattern; `reset()` returns to Idle without notifying
- ✅ State names aligned to 10-state specification: `Initializing`, `Idle`, `Hover`, `Active`, `Processing`, `Streaming`, `Success`, `Notification`, `Sleeping`, `Error`
- ✅ `TRANSITIONS` map updated to cover all 10 states with correct edges
- ✅ `OrbEvents` renamed: voice terminology removed; `StreamingStarted/Finished`, `ProcessingStarted/Finished`, `InputStarted/Finished` in place
- ✅ `LivingOrb.tsx` CSS class names verified correct (`orb-state-*` uses enum string values)

---

### Desktop Presence

- ✅ `DesktopPresenceService` — initialize, shutdown, registerOverlay, unregisterOverlay, getOverlay, listOverlays
- ✅ `Overlay` interface — id, initialize, show, hide, destroy, isVisible
- ✅ `OverlayRegistry` — Map-backed with duplicate-id guard
- ✅ `DesktopPresenceContext` + `DesktopPresenceProvider`
- ✅ `OrbController` — implements Overlay, owns OrbStateMachine, hover state transitions, subscribe pattern
- ✅ Unit tests: `DesktopPresenceService`, `OrbController`, `OverlayRegistry`

---

### Glass Prompt

Nothing in this section exists in the current codebase.

- ☐ `GlassPrompt` overlay component with frosted glass visual (backdrop-filter or Tauri window-vibrancy)
- ☐ Opens on Living Orb click
- ☐ Opens on Ctrl+K global keyboard shortcut
- ☐ Auto-focuses prompt input field on open
- ☐ Prompt input wired to `ConversationService` (with `ContextSnapshot` passed through)
- ☐ Streamed response displayed in Glass Prompt
- ☐ Markdown rendering in Glass Prompt
- ☐ Close on Escape or outside-click
- ☐ Conversation state preserved when Glass Prompt closes
- ☐ Open / close animation (Framer Motion)
- ☐ Living Orb transitions: `Idle` → `Active` when Glass Prompt opens
- ☐ Orb state tracks conversation: `Active` → `Processing` → `Streaming` → `Success` / `Error` → `Idle`
- ☐ Unit tests for `GlassPrompt` component
- ☐ Integration tests: `GlassPrompt` ↔ `ConversationService` ↔ `OrbController` state flow

---

### Workspace Transition

Nothing in this section exists in the current codebase.

- ☐ `WorkspacePage` implemented (replaces `PlaceholderPage`)
- ☐ Trigger: Glass Prompt offers "Open in Workspace" when conversation becomes lengthy
- ☐ Conversation history transferred from Glass Prompt to Workspace without loss
- ☐ Active streaming continues through the transition without cancellation
- ☐ Glass Prompt closes gracefully during transition
- ☐ Focus management: Workspace receives focus after transition
- ☐ Return path from Workspace to compact orb-only mode
- ☐ Integration tests for state handoff and streaming continuity

---

### Animation System

- ✅ `OrbAnimationController` — subscribes `OrbStateMachine` to `OrbAnimationDriver` interface
- ✅ `OrbAnimationDriver` interface
- ✅ `OrbEvents` typed event set — renamed to match corrected state names
- ☐ CSS animations defined for all 10 orb states (`orb-state-idle`, `orb-state-hover`, `orb-state-processing`, `orb-state-streaming`, `orb-state-success`, `orb-state-active`, `orb-state-initializing`, `orb-state-notification`, `orb-state-sleeping`, `orb-state-error`)
- ☐ Concrete `OrbAnimationDriver` implementation (Framer Motion variants or CSS keyframes)
- ☐ Idle pulse animation (subtle, continuous)
- ☐ Processing animation (activity indicator)
- ☐ Streaming animation (content flow indicator)
- ☐ Success animation (brief positive feedback, returns to Idle)
- ☐ Error animation (distinct negative feedback)
- ☐ Glass Prompt open / close transition animations
- ☐ Workspace transition animation

---

### Windows Native Experience

- ☐ Frosted glass / acrylic material on Glass Prompt (CSS `backdrop-filter` or Tauri `window-vibrancy`)
- ☐ Minimum window dimensions enforced in `tauri.conf.json`
- ☐ Multi-monitor orb positioning (monitor boundary detection at runtime)
- ☐ Ctrl+K global shortcut functional when companion is not the foreground window
- ☐ Keyboard navigation validated end-to-end through Orb → Glass Prompt → Workspace flow
- ☐ `prefers-reduced-motion` respected in all orb and Glass Prompt animations
- ☐ High contrast mode tested

---

### Testing

- ✅ `OrbStateMachine` unit tests (all valid and invalid transitions, subscribers, reset)
- ✅ `orbStore` unit tests (position defaults, `setPosition`, viewport clamping)
- ✅ `LivingOrb` component tests (render, accessibility label, CSS state class, data attribute, interactions)
- ✅ `OrbLayer` integration tests (registration, hover propagation, unmount cleanup)
- ✅ `useOrbDrag` hook tests (delta calculation, pointer event handling)
- ✅ `DesktopPresenceService` unit tests (initialize idempotency, shutdown, overlay lifecycle)
- ✅ `OrbController` unit tests (registration, show/hide, hover FSM, subscribe/dispose)
- ✅ `OverlayRegistry` unit tests (register, get, unregister, clear, duplicate error)
- ✅ All existing tests updated after `OrbState` rename
- ✅ `NullContextEngine` unit tests
- ✅ `NullRetrievalBroker` unit tests
- ✅ `NullProjectKnowledgeRepository` unit tests
- ☐ `GlassPrompt` component unit tests
- ☐ `GlassPrompt` ↔ `ConversationService` integration tests
- ☐ Workspace transition integration tests
- ☐ Manual desktop integration test checklist executed: overlay stability, Ctrl+K focus acquisition, multi-monitor positioning, streaming continuity during window transition

---

### Documentation

- ✅ PRD completed
- ✅ TDD completed
- ✅ Visual Design Language completed
- ✅ Implementation Plan completed
- ✅ Acceptance Criteria completed
- ✅ Architecture diagrams updated (Retrieval Broker call direction resolved)
- ✅ `ContextSnapshot`, `RetrievalQuery`, `Project` types defined in documentation
- ☐ ADR-007 (IPC Communication) created
- ☐ Directory layout decision recorded in documentation
- ☐ Completion Checklist items updated as implementation proceeds

---

# Next Phase

Proceed to:

**Phase 01 – AI Integration**

The next phase connects the desktop application to real AI services through Azure API Management, implementing the APIM provider, RAG pipeline, embedding generation, streaming responses, and conversation persistence.
