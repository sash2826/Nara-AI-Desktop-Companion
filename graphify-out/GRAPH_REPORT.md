# Graph Report - Enterprise-AI-Companion  (2026-08-26)

## Corpus Check
- 431 files · ~252,329 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3535 nodes · 7559 edges · 242 communities (161 shown, 81 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 767 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f46755f2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- lib.rs
- plugin_manager.py
- GraphProvider
- app.py
- BackupService
- GraphQueryService
- GraphScorePort
- IPCClient.ts
- Entity
- Technology Stack
- MessageBubble.tsx
- cn
- compilerOptions
- StatusBar.tsx
- make_scorer
- context_assembler.py
- SheetSpec
- OrbController.ts
- HybridSearchOrchestrator
- dependencies
- SearchPage.tsx
- SQLiteGraphProvider
- NullGraphProvider
- DocumentRepository
- workspaceStore.ts
- conversations.py
- indexing.py
- EmbeddingService
- HybridSearchResult
- Implementation Documentation Overview
- Phase-09-File-Organisation-New-Files.md
- TestCanonicalName
- HybridSearchOrchestrator
- Search Pipeline Architecture
- bundle
- file_indexer.py
- GraphCanvas.tsx
- KeywordSearchProvider
- Phase-08-Orb-Native-Shell.md
- KnowledgeGraphService
- ConversationRepository
- OrbAnimationEngine.tsx
- QueryPreprocessor
- LivingOrb.tsx
- TextChunker
- _make_watcher
- .upsert_entity
- GraphStateRepository
- ConversationService.ts
- OrbController
- OrbState
- Neo4jProvider
- _mock_db_app
- _make_result
- App.tsx
- retrieval/index.ts
- conversation_repository.py
- WatcherService
- components.json
- APIMProvider.test.ts
- Graphify Knowledge Graph Tool
- TestGraphStateRepository
- ChunkRepository
- auth.rs
- TestEntityExtractor
- get_config
- services/orb/index.ts
- OrganiseTab.tsx
- AssistantWidget.tsx
- test_placement_scorer.py
- useConversation.ts
- Phase-10-File-Organisation-Existing-Files.md
- test_file_watcher.py
- SettingsPage.tsx
- ContextSnapshot
- NotificationService
- query_preprocessor.py
- APIMProvider
- plugins.py
- PluginManager
- _make_client
- organisation.py
- Engineering Specification (CLAUDE.md)
- recommendationGroups.ts
- permissions
- scripts
- .score_all
- PluginRegistry
- ConversationCallbacks
- compilerOptions
- server.py
- _detect_intent
- TestEmbeddingsEndpoint
- Neo4j Graph Database
- plugin_loader.py
- DebounceHandler
- TestExpand
- TestNormalise
- TestDebounceHandler
- package.json
- ConversationServiceProvider.tsx
- NullProjectKnowledgeRepository.ts
- IndexingStatusPanel.tsx
- orb.py
- TestTokenise
- TestRemoveStopWords
- PluginManifest
- TestLooksLikeTypo
- FileIndexer
- test_package.py
- FastAPI
- database.py
- score_benchmark.py
- main
- generate_search_pipeline_pdf.py
- Capability Layer
- Benchmark Scorecard — File Organisation
- Python Sidecar (FastAPI)
- Presentation Layer
- File Indexing Capability
- HomePage.tsx
- lint-staged
- Enterprise AI Companion App Icon (main)
- WorkspacePage.tsx
- .process
- BFS Graph Traversal Query
- .extract_text
- Tauri + React + Typescript
- Settings Page
- vite.config.ts
- plugins/__init__.py
- SearchEnricherPlugin
- Plugin System
- devDependencies
- OrbLayer.tsx
- .__init__
- eslint-plugin-react-hooks
- husky
- jiti
- lint-staged
- @eslint/js
- @radix-ui/react-dialog
- @radix-ui/react-dropdown-menu
- @radix-ui/react-label
- @radix-ui/react-separator
- @radix-ui/react-slot
- OrganiseDashboard.tsx
- @radix-ui/react-toast
- @radix-ui/react-tooltip
- @tauri-apps/cli
- @testing-library/react
- @types/node
- @types/react
- .log
- Volvo Group Abbreviations Reference
- vite-tsconfig-paths
- HybridRerankAdapter
- vitest
- @vitest/ui
- tailwind.config.ts
- pre-commit
- Project Changelog
- TypeScript
- Vite Build Tool Logo
- React Framework Logo
- App Icon 128x128@2x
- App Icon Square 107x107
- App Icon Square 142x142
- App Icon Square 150x150
- App Icon Square 284x284
- App Icon Square 30x30
- App Icon Square 310x310
- App Icon Square 44x44
- App Icon Square 71x71
- App Icon Square 89x89
- enterprise-ai-companion
- Enterprise AI Companion README
- benchmark_downloads.py
- MainContent.tsx
- test_conversation_repository.py
- IPCClient
- BackupSettings.tsx
- Passive Background Suggester (Phase 10 deferral)
- Volvo IT Terminology Glossary
- APIMProvider.ts
- get_db
- @radix-ui/react-avatar
- eslint-plugin-react-refresh
- _is_excluded
- IndexedDocument
- RecentFilesList.tsx
- TestWatcherServiceFolders
- .cancel_all
- eslint-config-prettier
- ._summarise
- .__init__
- .search
- clsx
- eslint-plugin-react
- organisation/__init__.py
- @fontsource-variable/inter
- @fontsource-variable/source-serif-4
- limit_request_body
- manifest.json
- lucide-react
- postcss
- test_api.py
- react-dom
- react-markdown
- remark-gfm
- @types/react-dom
- clear_pending.py
- tailwind-merge
- eac_benchmark/__init__.py
- tailwindcss
- @tauri-apps/plugin-dialog
- @tauri-apps/plugin-http
- jsdom
- prettier
- @radix-ui/react-scroll-area
- @radix-ui/react-switch
- @testing-library/jest-dom
- @types/d3-force
- typescript-eslint
- vite

## God Nodes (most connected - your core abstractions)
1. `cn()` - 136 edges
2. `EmbeddingService` - 70 edges
3. `NullGraphProvider` - 68 edges
4. `FileIndexer` - 66 edges
5. `DocumentRepository` - 58 edges
6. `AppState` - 54 edges
7. `Entity` - 50 edges
8. `Relationship` - 48 edges
9. `GraphProvider` - 48 edges
10. `ConversationRepository` - 44 edges

## Surprising Connections (you probably didn't know these)
- `AI Agent UI Design Mockup` --conceptually_related_to--> `Search Pipeline Architecture`  [INFERRED]
  UI-Design-Mockup/AI_Agent.png → docs/Search-Pipeline-Architecture.pdf
- `AI Agent UI Design Mockup` --conceptually_related_to--> `useConversation.ts`  [INFERRED]
  UI-Design-Mockup/AI_Agent.png → docs/Search-Pipeline-Architecture.pdf
- `FileIndexer` --semantically_similar_to--> `File Indexing Capability`  [INFERRED] [semantically similar]
  docs/BACKLOG.md → backend/README.md
- `run_query()` --calls--> `chat_complete()`  [INFERRED]
  scripts/benchmark_query.py → backend/src/enterprise_ai_companion/capabilities/ai/llm_client.py
- `main()` --calls--> `SQLiteGraphProvider`  [INFERRED]
  scripts/benchmark_audit.py → backend/src/enterprise_ai_companion/capabilities/graph/sqlite_graph_provider.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Enterprise AI Companion Layered Architecture Stack** — docs_architecture_application_layers_presentation_layer, docs_architecture_application_layers_application_layer, docs_architecture_application_layers_capability_layer, docs_architecture_application_layers_domain_layer, docs_architecture_application_layers_infrastructure_layer, docs_architecture_application_layers_external_systems [EXTRACTED 1.00]
- **Multi-Database Storage Strategy** — _claude_claude_sqlite_db, _claude_claude_neo4j_db, _claude_claude_qdrant_db [EXTRACTED 1.00]
- **GraphProvider Implementations** — docs_backlog_null_graph_provider, docs_backlog_neo4j_provider, docs_backlog_sqlite_graph_provider [EXTRACTED 1.00]
- **Architecture Foundation Documents** — docs_architecture_system_overview, docs_architecture_capability_model, docs_architecture_repository_layout, docs_architecture_technology_stack [INFERRED 0.95]
- **Polyglot Storage Technologies** — docs_architecture_technology_stack_sqlite, docs_architecture_technology_stack_neo4j, docs_architecture_technology_stack_qdrant [EXTRACTED 1.00]
- **Enterprise AI Companion Capabilities** — docs_architecture_capability_model_file_intelligence, docs_architecture_capability_model_search_retrieval, docs_architecture_capability_model_knowledge_management, docs_architecture_capability_model_ai_services, docs_architecture_capability_model_conversation, docs_architecture_capability_model_workspace_management, docs_architecture_capability_model_automation, docs_architecture_capability_model_settings_configuration, docs_architecture_capability_model_system_administration [EXTRACTED 1.00]
- **Cross-Cutting Infrastructure Concerns** — docs_decisions_adr_010_logging_and_observability_centralized_observability, docs_decisions_adr_012_error_handling_strategy_centralized_error_handling, docs_decisions_adr_009_authentication_and_security_layered_security, docs_decisions_adr_006_configuration_management_configuration_service [INFERRED 0.85]
- **Core AI Conversation Pipeline** — docs_implementation_phase_00_assistant_experience_glass_prompt, docs_implementation_phase_00_assistant_experience_conversation_service, docs_implementation_phase_00_assistant_experience_context_engine, docs_implementation_phase_00_assistant_experience_retrieval_broker, docs_implementation_phase_00_assistant_experience_llm_provider [EXTRACTED 1.00]
- **Hybrid Search Pipeline** — docs_implementation_phase_02_knowledge_search_query_preprocessor, docs_implementation_phase_02_knowledge_search_keyword_search_provider, docs_implementation_phase_02_knowledge_search_qdrant_search_provider, docs_implementation_phase_02_knowledge_search_hybrid_search_orchestrator, docs_implementation_phase_02_knowledge_search_rrf [EXTRACTED 1.00]
- **Knowledge Graph Backend Providers** — docs_implementation_phase_05_knowledge_graph_graph_provider, docs_implementation_phase_05_knowledge_graph_sqlite_graph_provider, docs_implementation_phase_02_knowledge_search_knowledge_graph_service [EXTRACTED 1.00]
- **Phase 04 Intelligence Chain (Context → Memory → Rerank → Cite)** — docs_implementation_phase_04_ai_context_intelligence_context_assembler, docs_implementation_phase_04_ai_context_intelligence_conversation_memory_service, docs_implementation_phase_04_ai_context_intelligence_heuristic_reranker, docs_implementation_phase_04_ai_context_intelligence_citation_chip [EXTRACTED 1.00]
- **Frontend Service Layer (Search, Settings, Workspace)** — frontend_src_services_search_readme_search_service, frontend_src_services_settings_readme_settings_service, frontend_src_services_workspace_readme_workspace_service [INFERRED 0.85]
- **Seven-Stage Search Pipeline Flow** — docs_search_pipeline_architecture_stage_0_indexing, docs_search_pipeline_architecture_stage_1_query_preprocessing, docs_search_pipeline_architecture_stage_2_hybrid_search, docs_search_pipeline_architecture_stage_3_rrf_merge, docs_search_pipeline_architecture_stage_4_heuristic_reranker, docs_search_pipeline_architecture_stage_5_quality_filter, docs_search_pipeline_architecture_stage_6_citation_xref [EXTRACTED 1.00]
- **Enterprise AI Companion Brand Icon Variants** — frontend_src_tauri_icons_icon_app_icon, frontend_src_tauri_icons_32x32_app_icon, frontend_src_tauri_icons_128x128_app_icon, frontend_src_tauri_icons_128x128_2x_app_icon, frontend_src_tauri_icons_square107x107logo_app_icon, frontend_src_tauri_icons_square142x142logo_app_icon, frontend_src_tauri_icons_square150x150logo_app_icon, frontend_src_tauri_icons_square284x284logo_app_icon, frontend_src_tauri_icons_square30x30logo_app_icon, frontend_src_tauri_icons_square310x310logo_app_icon, frontend_src_tauri_icons_square44x44logo_app_icon, frontend_src_tauri_icons_square71x71logo_app_icon, frontend_src_tauri_icons_square89x89logo_app_icon, frontend_src_tauri_icons_storelogo_app_icon [INFERRED 0.95]
- **Frontend Technology Stack (Tauri + Vite + React)** — frontend_public_tauri_tauri_logo, frontend_public_vite_vite_logo, frontend_src_assets_react_react_logo [INFERRED 0.95]
- **Hybrid Search Dual Provider (BM25 + Qdrant Cosine)** — docs_search_pipeline_architecture_bm25_fts5_keyword_search, docs_search_pipeline_architecture_qdrant_vector_store, docs_search_pipeline_architecture_reciprocal_rank_fusion [EXTRACTED 1.00]

## Communities (242 total, 81 thin omitted)

### Community 0 - "lib.rs"
Cohesion: 0.08
Nodes (109): App, Child, Client, accept_recommendation(), add_watched_folder(), AddFolderRequest, AppState, BackupResultResponse (+101 more)

### Community 1 - "plugin_manager.py"
Cohesion: 0.16
Nodes (14): FileProcessorPlugin, ABC, Abstract base classes defining the extension points available to plugins. A…, Extract plain text from files of a custom type. Registered plugins are…, Return lowercase dot-prefixed extensions, e.g. ``frozenset({".abc"})``., Transform extracted text before it is chunked and embedded. Plugins in this…, Return the (possibly modified) text. *file_path* is provided as context only;…, Augment hybrid search results after the core ranking step. NOTE: Wiring into… (+6 more)

### Community 2 - "GraphProvider"
Cohesion: 0.07
Nodes (14): GraphProvider, ABC, Defines the contract for all graph storage backends., Set up indexes and constraints. Safe to call multiple times., Create or update an entity node., Create or update a relationship between two entity nodes., Return the entity and its neighbourhood up to `depth` hops., Return entities whose names contain *query* (case-insensitive). Each dict has… (+6 more)

### Community 3 - "app.py"
Cohesion: 0.03
Nodes (59): AzureTokenMiddleware, _build_graph_provider(), lifespan(), _purge_orphaned_folder_documents(), FastAPI application for the Enterprise AI Companion backend., Open all stores on startup; close them on shutdown., Reject requests that lack the per-session IPC shared secret. The token is…, Extract the Azure AD access token from X-Azure-Token and store it in a… (+51 more)

### Community 4 - "BackupService"
Cohesion: 0.05
Nodes (39): BackupResultResponse, BackupSummaryResponse, create_backup(), CreateBackupRequest, delete_backup(), DeleteBackupResponse, _get_service(), list_backups() (+31 more)

### Community 5 - "GraphQueryService"
Cohesion: 0.08
Nodes (45): ConnectedDocumentsResponse, _entity_to_response(), EntityResponse, EntitySearchResponse, find_path(), get_connected_documents(), get_entity_context(), get_graph_visualization() (+37 more)

### Community 6 - "GraphScorePort"
Cohesion: 0.09
Nodes (23): Production adapters for PlacementScorer ports. Each adapter satisfies one port…, Return canonical entity names for *folder_path*, expanded 1 hop. Always…, Return unique parent directories inferred from indexed file paths. Ranked by…, Satisfies GraphScorePort using direct SQLite queries. Owns all SQL against…, Return canonical names for entities in *document_id*, expanded 1 hop. Falls…, SqliteGraphScoreAdapter, expand_for_matching(), filename_bigrams() (+15 more)

### Community 7 - "IPCClient.ts"
Cohesion: 0.03
Nodes (18): ConversationMemory, ConversationSummary, EmbedResponse, GraphContextResponse, GraphEntityItem, GraphHealthResponse, GraphRelationshipItem, HealthResponse (+10 more)

### Community 8 - "Entity"
Cohesion: 0.08
Nodes (39): Knowledge graph enrichment service. Runs after entity and relationship…, Extracts named entities from text using a structured LLM call. Replaces the…, Entity, EntityType, GraphContext, Enum, str, Shared domain models for the knowledge graph capability. (+31 more)

### Community 9 - "Technology Stack"
Cohesion: 0.08
Nodes (45): Capability Model, AI Services Capability, Automation Capability, Conversation Capability, File Intelligence Capability, Knowledge Management Capability, Search & Retrieval Capability, Settings & Configuration Capability (+37 more)

### Community 10 - "MessageBubble.tsx"
Cohesion: 0.07
Nodes (36): CitationChip(), CitationChipProps, ConversationView(), ConversationViewProps, CARDS, EmptyChatState(), EmptyChatStateProps, FilePathChip() (+28 more)

### Community 11 - "cn"
Cohesion: 0.07
Nodes (43): AssistantAvatar(), AssistantAvatarProps, SIZE_CLASSES, AssistantFooter(), AssistantFooterProps, AttachmentButton(), AttachmentButtonProps, CONTEXT_ITEMS (+35 more)

### Community 12 - "compilerOptions"
Cohesion: 0.05
Nodes (39): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+31 more)

### Community 13 - "StatusBar.tsx"
Cohesion: 0.10
Nodes (24): STATUS_CLASSES, STATUS_LABELS, StatusIndicator(), StatusIndicatorProps, StatusVariant, MODES, ThemeToggle(), ThemeToggleProps (+16 more)

### Community 14 - "make_scorer"
Cohesion: 0.14
Nodes (9): make_scorer(), asyncio, TestCombinedScore, TestDiscoverCandidateFolders, TestGraphGate, TestGraphScore, TestLabels, TestScoreAll (+1 more)

### Community 15 - "context_assembler.py"
Cohesion: 0.09
Nodes (28): ContextAssembler, ContextChunk, ContextPayload, Connection, QdrantClient, Context assembly service for the AI retrieval pipeline. Wraps the hybrid search…, Retrieve and assemble context chunks for the given query. Pipeline: 1. Hybrid…, Supplement vector-retrieved chunks with graph-neighbour chunks. For each token… (+20 more)

### Community 16 - "SheetSpec"
Cohesion: 0.05
Nodes (99): Block, DocSpec, _ensure_dir(), Shared document-building helpers for the file-organization benchmark corpus.…, Declarative description of a single worksheet., Declarative description of a single slide., Declarative description of a single document., SheetSpec (+91 more)

### Community 17 - "OrbController.ts"
Cohesion: 0.10
Nodes (10): DesktopPresenceContext, DesktopPresenceProvider(), DesktopPresenceProviderProps, DesktopPresenceService, ORB_OVERLAY_ID, OrbControllerState, OrbStateListener, Overlay (+2 more)

### Community 18 - "HybridSearchOrchestrator"
Cohesion: 0.13
Nodes (30): _get_db(), hybrid_search(), HybridSearchRequest, HybridSearchResponse, HybridSearchResultItem, keyword_search(), KeywordSearchRequest, KeywordSearchResponse (+22 more)

### Community 19 - "dependencies"
Cohesion: 0.12
Nodes (17): autoprefixer, class-variance-authority, d3-force, dependencies, autoprefixer, class-variance-authority, d3-force, framer-motion (+9 more)

### Community 20 - "SearchPage.tsx"
Cohesion: 0.09
Nodes (30): SuggestedQueries(), SuggestedQueriesProps, EmptySearchState(), EmptySearchStateProps, SearchFilters(), SearchFiltersProps, TOP_K_OPTIONS, SearchInput() (+22 more)

### Community 21 - "SQLiteGraphProvider"
Cohesion: 0.07
Nodes (27): Connection, Insert or update a directed relationship edge., Create SIMILAR_TO edges between entities that share a canonical name across…, Remove all entities (and cascade-delete their relationships) for a document., Case-insensitive substring search over entity names., Return document IDs reachable within 2 hops from *entity_name*. Uses a…, Return ``{"nodes": [...], "edges": [...]}`` for the graph UI. When…, Return entity IDs reachable from *entity_name* within *depth* hops. (+19 more)

### Community 22 - "NullGraphProvider"
Cohesion: 0.11
Nodes (5): NullGraphProvider, provider(), fixture, Tests for NullGraphProvider — verifies the no-op contract., TestNullGraphProvider

### Community 23 - "DocumentRepository"
Cohesion: 0.09
Nodes (20): DocumentRepository, IndexedDocument, _like_prefix(), Connection, Repository for indexed document metadata stored in SQLite., Return a LIKE pattern that matches any file_path under folder_path. Strips…, Update the stored file_path without touching any other record., Return all documents belonging to workspace_path. Uses both exact… (+12 more)

### Community 24 - "workspaceStore.ts"
Cohesion: 0.13
Nodes (17): DocumentFilters(), DocumentFiltersProps, EXTENSION_OPTIONS, SORT_OPTIONS, WatcherStatusBadgeProps, WatchedFolder, WatcherStatus, WorkspaceService (+9 more)

### Community 25 - "conversations.py"
Cohesion: 0.15
Nodes (22): ConversationMemoryResponse, ConversationResponse, ConversationSummaryResponse, get_conversation_memory(), list_conversations(), load_conversation(), MessageResponse, BaseModel (+14 more)

### Community 26 - "indexing.py"
Cohesion: 0.11
Nodes (26): cancel_indexing(), clear_indexing_errors(), get_indexing_status(), IndexingErrorResponse, IndexingStatusResponse, list_indexing_errors(), Any, BaseModel (+18 more)

### Community 27 - "EmbeddingService"
Cohesion: 0.10
Nodes (13): EmbeddingService, Generates dense text embeddings using bge-small-en-v1.5 locally via ONNX…, Return a single embedding vector for the given text. Args: text: The input…, Return embedding vectors for a list of texts. Args: texts: A non-empty list of…, Connection, QdrantClient, fixture, Unit tests for EmbeddingService. These tests load the real BGE-M3 model via… (+5 more)

### Community 28 - "HybridSearchResult"
Cohesion: 0.22
Nodes (6): HybridSearchResult, A single result from the hybrid search pipeline. The rrf_score is the combined…, _make_client(), TestClient, Return a TestClient with mocked app.state attributes., TestHybridSearchEndpoint

### Community 29 - "Implementation Documentation Overview"
Cohesion: 0.10
Nodes (29): Confidence Model, Context Engine, ContextSnapshot, Conversation Service, Desktop Companion, Desktop Presence Layer, Glass Prompt, Living Orb (+21 more)

### Community 30 - "Phase-09-File-Organisation-New-Files.md"
Cohesion: 0.10
Nodes (20): Architecture, Completion Criteria, Confidence Scoring Formula, Deliverables, Dependencies, Design Decisions, Downloads Watch, File Move and Record Update (+12 more)

### Community 31 - "TestCanonicalName"
Cohesion: 0.18
Nodes (6): canonical_name(), EnrichmentService, Return a normalised lowercase key suitable for duplicate detection. Steps: 1.…, Post-extraction enrichment for the knowledge graph. Supports…, Run the full enrichment pipeline — merge duplicates across all entity types., TestCanonicalName

### Community 32 - "HybridSearchOrchestrator"
Cohesion: 0.07
Nodes (28): AbbreviationExtractor, FileIndexer, HybridSearchOrchestrator, KeywordSearchProvider (FTS5), KnowledgeGraphService, QdrantSearchProvider, QueryPreprocessor, Reciprocal Rank Fusion (RRF) (+20 more)

### Community 33 - "Search Pipeline Architecture"
Cohesion: 0.12
Nodes (27): BAAI/bge-small-en-v1.5 Embedding Model (384-dim), BM25 Keyword Search (SQLite FTS5), Character Bigram Cosine Reranker, chunk_repository.py, context_assembler.py, embedding_service.py, file_indexer.py, hybrid_orchestrator.py (+19 more)

### Community 34 - "bundle"
Cohesion: 0.05
Nodes (37): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+29 more)

### Community 35 - "file_indexer.py"
Cohesion: 0.08
Nodes (22): AbbreviationRepository, Connection, Repository for persisting and querying discovered abbreviations. Abbreviation…, Async repository for the ``abbreviations`` table. Args: conn: An open…, Persist a batch of abbreviation matches for a single document. Uses ``INSERT OR…, Remove all abbreviation rows for the given document. Called before re-indexing…, Load all discovered abbreviations across every document. Returns a mapping…, IndexingResult (+14 more)

### Community 36 - "GraphCanvas.tsx"
Cohesion: 0.14
Nodes (21): confidenceColor(), confidenceLabel(), EntityCard(), EntityCardProps, drawArrow(), drawFrame(), ENTITY_COLORS, entityColor() (+13 more)

### Community 37 - "KeywordSearchProvider"
Cohesion: 0.08
Nodes (20): _escape_fts5_query(), KeywordSearchProvider, _normalise_bm25(), Connection, Keyword search provider backed by SQLite FTS5., Build an FTS5 MATCH expression from a natural language query. Each token is…, Convert a raw SQLite BM25 score (negative, unbounded) to (0, 1]. SQLite's…, Full-text keyword search over indexed document chunks using SQLite FTS5. The… (+12 more)

### Community 38 - "Phase-08-Orb-Native-Shell.md"
Cohesion: 0.10
Nodes (19): Animation States, Architecture, Completion Criteria, Deliverables, Dependencies, Design Decisions, Interaction Model, Modified Files (+11 more)

### Community 39 - "KnowledgeGraphService"
Cohesion: 0.16
Nodes (8): KnowledgeGraphService, Orchestrates entity extraction and graph persistence for indexed documents.…, Extract entities/relationships from each chunk and persist to the graph. After…, Remove all graph nodes and relationships sourced from this document., Create SIMILAR_TO edges between entities sharing a canonical name across…, fixture, service(), TestBuildFromChunks

### Community 40 - "ConversationRepository"
Cohesion: 0.13
Nodes (8): ConversationRepository, Atomically increment turn_count and return the new value., Persist a compressed summary for the conversation., Async repository for conversation and message persistence., TestGetOrCreateConversation, TestListConversations, TestLoadConversation, TestSaveMessage

### Community 41 - "OrbAnimationEngine.tsx"
Cohesion: 0.17
Nodes (21): OrbIconProps, ORB_BORDER_COLOR, ORB_GRADIENT_FROM, ORB_GRADIENT_MID, ORB_GRADIENT_TO, ORB_HIGHLIGHT_COLOR, ORB_HIGHLIGHT_SIZE, ORB_RADIUS (+13 more)

### Community 42 - "QueryPreprocessor"
Cohesion: 0.17
Nodes (6): QueryPreprocessor, QueryPreprocessorConfig, Transforms a raw user query into a structured ProcessedQuery. Designed to be…, Replace the dynamic expansion set with entries from discovered abbreviations.…, Feature flags for the preprocessing pipeline., TestQueryPreprocessor

### Community 43 - "LivingOrb.tsx"
Cohesion: 0.12
Nodes (17): LivingOrb(), LivingOrbProps, OrbContainer(), OrbContainerProps, OrbIcon(), DragOrigin, UseOrbDragOptions, UseOrbDragResult (+9 more)

### Community 44 - "TextChunker"
Cohesion: 0.15
Nodes (7): Splits plain text into overlapping character-based chunks for embedding., Splits text into overlapping chunks, preferring sentence boundaries. Args:…, Return a list of (content, char_start, char_end) tuples. Chunks are at most…, Return the character position of the last sentence break in text, or 0., TextChunker, Unit tests for TextChunker., TestChunker

### Community 45 - "_make_watcher"
Cohesion: 0.19
Nodes (11): _client_with_watcher(), _make_watcher(), TestClient, WatchedFolder, Endpoint tests for the /watcher router. Injects a mock WatcherService into…, Build a minimal WatcherService mock for injection into app.state., Return a TestClient that has watcher injected after lifespan starts., TestAddFolder (+3 more)

### Community 46 - ".upsert_entity"
Cohesion: 0.50
Nodes (3): _canonical(), Inline canonical-name helper (mirrors enrichment_service.canonical_name). Kept…, Insert or update an entity node. Uses INSERT OR REPLACE so re-indexing the same…

### Community 47 - "GraphStateRepository"
Cohesion: 0.09
Nodes (30): add_watched_folder(), AddFolderRequest, _cancel_indexing_tasks(), get_watcher_status(), list_watched_folders(), _purge_folder_documents(), BaseModel, delete (+22 more)

### Community 48 - "ConversationService.ts"
Cohesion: 0.18
Nodes (6): ConversationServiceContext, LLMProvider, ConversationService, ConversationTurn, NARA_TOOLS, READ_TOOL_NAMES

### Community 49 - "OrbController"
Cohesion: 0.18
Nodes (3): OrbController, makeControllableProvider(), renderIntegration()

### Community 50 - "OrbState"
Cohesion: 0.21
Nodes (5): OrbAnimationController, OrbAnimationDriver, OrbState, OrbStateMachine, TRANSITIONS

### Community 51 - "Neo4jProvider"
Cohesion: 0.09
Nodes (11): Neo4jProvider, Create or update a directed relationship between two entity nodes. Both nodes…, Return ``{"nodes": [...], "edges": [...]}`` for the graph UI. When…, Return entities whose names contain *query* (case-insensitive substring). Args:…, Return document IDs of all entities reachable (up to 2 hops) from entity_name., Remove all entity nodes (and their relationships) sourced from document_id., Knowledge graph backend powered by Neo4j Community 5.x. Relationships are…, Merge entity node — creates on first call, updates on subsequent calls. (+3 more)

### Community 52 - "_mock_db_app"
Cohesion: 0.18
Nodes (10): ConversationSummary, Return all conversations, most recent first, with their message count., _make_message(), _mock_db_app(), Tests for the conversations FastAPI endpoints using an in-memory database., Return a TestClient with a mock db in app.state., TestListConversationsEndpoint, TestLoadConversationEndpoint (+2 more)

### Community 53 - "_make_result"
Cohesion: 0.12
Nodes (13): Merge two ranked lists using Reciprocal Rank Fusion. Each chunk accumulates an…, Execute hybrid search and return merged results. Args: query: Preprocessed…, _rrf_merge(), Shared data models for the search capability., SearchResult, _make_result(), asyncio, Tests for the hybrid search orchestrator and /search/hybrid endpoint. Covers… (+5 more)

### Community 54 - "App.tsx"
Cohesion: 0.28
Nodes (6): App(), AppShell(), root, LayoutProvider(), LayoutProviderProps, OrbWindow()

### Community 55 - "retrieval/index.ts"
Cohesion: 0.29
Nodes (9): LocalFileConnector, OneDriveConnector, NullRetrievalBroker, DocumentFragment, RetrievalBroker, RetrievalQuery, RetrievalResult, ANY_QUERY (+1 more)

### Community 56 - "conversation_repository.py"
Cohesion: 0.15
Nodes (10): ConversationMemoryState, Message, Conversation persistence repository. Provides async CRUD operations over the…, Persist a message, creating the parent conversation if needed., Return all messages for a conversation, oldest first., Return the turn_count and summary for a conversation. Creates the conversation…, Return up to `limit` messages, oldest first, for summarisation., Memory state for a single conversation, read from the conversations table. (+2 more)

### Community 57 - "WatcherService"
Cohesion: 0.13
Nodes (12): Manages the watchdog Observer and the set of watched folders. Persists the…, Load persisted folders and start the watchdog Observer. Safe to call from…, Async start path — used when start() is called from inside the event loop., Register a new folder for watching. Triggers an immediate initial index., Persist a folder as watched and start the filesystem watch. Unlike add_folder,…, Unregister a folder and stop watching it., Return all registered watched folders., Remove index records for files that no longer exist on disk. Called at startup… (+4 more)

### Community 58 - "components.json"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 59 - "APIMProvider.test.ts"
Cohesion: 0.22
Nodes (4): APIMError, makeSSEStream(), mockSSEResponse(), TEST_CONFIG

### Community 60 - "Graphify Knowledge Graph Tool"
Cohesion: 0.12
Nodes (17): Graphify Add URL Ingestion, Graphify Watch Folder Auto-Rebuild, MCP Server Graph Export, Wiki Export (Agent-Crawlable), Extraction Subagent Prompt, Cross-Repo Graph Merge, CLAUDE.md Graphify Integration, Post-Commit Auto-Rebuild Hook (+9 more)

### Community 61 - "TestGraphStateRepository"
Cohesion: 0.36
Nodes (3): Connection, Integration tests using an in-memory SQLite database., TestGraphStateRepository

### Community 62 - "ChunkRepository"
Cohesion: 0.10
Nodes (26): bulk_delete_documents(), BulkDeleteRequest, delete_document(), DocumentResponse, _is_system_document(), list_documents(), BaseModel, delete (+18 more)

### Community 63 - "auth.rs"
Cohesion: 0.22
Nodes (24): auth_check(), auth_get_token(), auth_login(), auth_logout(), AuthStateEvent, AzureTokenData, clear_keychain(), do_refresh() (+16 more)

### Community 64 - "TestEntityExtractor"
Cohesion: 0.08
Nodes (22): _coerce_entity_type(), EntityExtractor, _parse_json(), Any, Attempt to parse raw LLM output as JSON, stripping markdown fences., Extracts named entities from a text chunk via a structured LLM call. Usage:…, Return extracted entities from text. Returns [] on failure., ExtractedEntity (+14 more)

### Community 65 - "get_config"
Cohesion: 0.05
Nodes (47): DashboardStats, _get_stats(), get_suggested_queries(), BaseModel, Connection, get, post, Request (+39 more)

### Community 66 - "services/orb/index.ts"
Cohesion: 0.22
Nodes (15): ErrorOccurredEvent, HoverEnterEvent, HoverLeaveEvent, InputFinishedEvent, InputStartedEvent, NotificationReceivedEvent, OrbEvent, OrbEventType (+7 more)

### Community 67 - "OrganiseTab.tsx"
Cohesion: 0.14
Nodes (21): FolderGrid(), FolderGridProps, FolderTile(), FolderTileProps, aggregateCounts(), buildFolderTree(), findDeepestMatch(), findNodeByPath() (+13 more)

### Community 68 - "AssistantWidget.tsx"
Cohesion: 0.18
Nodes (13): AssistantWidget(), AssistantWidgetProps, ToolConfirmationCard(), ToolConfirmationCardProps, CachedSuggestions, DashboardState, loadCachedSuggestions(), pickRandom() (+5 more)

### Community 69 - "test_placement_scorer.py"
Cohesion: 0.14
Nodes (6): FakeGraphScorePort, FakeRerankPort, Unit tests for PlacementScorer. All tests use in-memory fakes — no database, no…, Returns pre-configured canonical sets without touching a database., Returns a fixed rerank score per (document_id, folder_path) pair., TestEntityExpansion

### Community 70 - "useConversation.ts"
Cohesion: 0.43
Nodes (6): cosine(), heuristicRerank(), ngramTf(), RankedCandidate, tokenise(), RetrievedChunk

### Community 71 - "Phase-10-File-Organisation-Existing-Files.md"
Cohesion: 0.10
Nodes (19): Architecture, Completion Criteria, Deduplication, Deliverables, Dependencies, Design Decisions, Modified Files, New Backend Modules (+11 more)

### Community 72 - "test_file_watcher.py"
Cohesion: 0.28
Nodes (6): db(), mock_indexer(), fixture, Unit tests for WatcherService and DebounceHandler., TestWatcherServiceStart, watcher_service()

### Community 73 - "SettingsPage.tsx"
Cohesion: 0.07
Nodes (34): AssistantHeader(), AssistantHeaderProps, resolveStatus(), AssistantStatus(), AssistantStatusProps, STATUS_CONFIG, StatusKind, AIProviderSettings() (+26 more)

### Community 74 - "ContextSnapshot"
Cohesion: 0.28
Nodes (4): ContextEngine, ContextSnapshot, NullContextEngine, WorkspaceContextEngine

### Community 75 - "NotificationService"
Cohesion: 0.23
Nodes (3): Notification, NotificationService, NullNotificationService

### Community 76 - "query_preprocessor.py"
Cohesion: 0.20
Nodes (9): _has_fuzzy_candidates(), Enum, str, Query preprocessing pipeline for the search subsystem. Each stage is…, Return True if any token looks like it might be a typo. Heuristics: - Token…, Broad classification of the user's search intent., SearchIntent, Unit tests for the query preprocessing pipeline. (+1 more)

### Community 78 - "plugins.py"
Cohesion: 0.26
Nodes (12): disable_plugin(), enable_plugin(), list_plugins(), PluginResponse, BaseModel, get, post, Request (+4 more)

### Community 79 - "PluginManager"
Cohesion: 0.13
Nodes (9): PluginManager, Toggle a plugin's enabled state in the database. NOTE: The change takes effect…, Manages the full plugin lifecycle: discovery, persistence, and access., Scan for plugins, register them, and return summary counts. Returns: A dict…, Return enabled plugins that implement ``FileProcessorPlugin``., Return enabled plugins that implement ``TextProcessorPlugin``., Return enabled plugins that implement ``SearchEnricherPlugin``., Return all registered plugins from the database. (+1 more)

### Community 80 - "_make_client"
Cohesion: 0.23
Nodes (6): _make_client(), TestClient, Tests for the /graph API endpoints using NullGraphProvider injected into…, Return a TestClient with NullGraphProvider pre-loaded into app.state., TestGetGraphEntity, TestGraphHealth

### Community 81 - "organisation.py"
Cohesion: 0.09
Nodes (34): accept_recommendation(), AcceptBody, AuditStatusResponse, CandidateItem, dismiss_recommendation(), get_audit_status(), list_pending(), pending_count() (+26 more)

### Community 82 - "Engineering Specification (CLAUDE.md)"
Cohesion: 0.23
Nodes (12): AI Provider Abstraction Layer, BGE-M3 Embeddings, Engineering Specification (CLAUDE.md), Enterprise AI Companion, OpenAI GPT-5 Mini, PaddleOCR, Qdrant Vector Store, Tauri Desktop Framework (+4 more)

### Community 83 - "recommendationGroups.ts"
Cohesion: 0.10
Nodes (31): rec(), OrbSvgFilters(), GroupSectionProps, OrbNotificationOverlay(), OrbQueryOverlay(), QueryState, SourceItem, THINKING_PHRASES (+23 more)

### Community 84 - "permissions"
Cohesion: 0.15
Nodes (12): description, identifier, permissions, $schema, windows, core:default, dialog:default, global-shortcut:allow-register (+4 more)

### Community 85 - "scripts"
Cohesion: 0.18
Nodes (11): scripts, build, dev, format, lint, lint:fix, preview, tauri (+3 more)

### Community 86 - ".score_all"
Cohesion: 0.18
Nodes (8): FolderScore, _label(), Any, Score for a single candidate folder., Return the combined score for a single folder against *document_id*. Used by…, Score every candidate folder and return up to 3 results sorted by score desc.…, Return (graph_s, rerank_s) without applying gate or weighting., Overlap coefficient on canonical entity names between new file and folder. Uses…

### Community 87 - "PluginRegistry"
Cohesion: 0.13
Nodes (9): Connection, Path, PluginRegistry, Connection, Return all registered plugins, ordered by display_name., Return True if the plugin exists and is enabled., Read/write access to the plugins table., Insert or update a plugin row from *manifest*. Preserves the existing… (+1 more)

### Community 89 - "compilerOptions"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, types, include (+2 more)

### Community 90 - "server.py"
Cohesion: 0.20
Nodes (9): PyInstaller entry point for the EAC backend sidecar. Must run BEFORE importing…, find_free_port(), _load_env_file(), Uvicorn startup and shutdown for the Enterprise AI Companion backend., Load key=value pairs from backend/.env into os.environ (if the file exists).…, Bind to port 0 so the OS assigns a free port, then release and return it., Start uvicorn on the given port (or a free OS-assigned port)., run() (+1 more)

### Community 91 - "_detect_intent"
Cohesion: 0.33
Nodes (3): _detect_intent(), Classify the query intent from the token set using signal words., TestDetectIntent

### Community 92 - "TestEmbeddingsEndpoint"
Cohesion: 0.21
Nodes (4): _patch_service(), Tests for the POST /embeddings FastAPI endpoint. Uses FastAPI's TestClient…, Patch the EmbeddingService singleton used by the router., TestEmbeddingsEndpoint

### Community 93 - "Neo4j Graph Database"
Cohesion: 0.22
Nodes (9): Neo4j Graph Database, SQLite Database, Neo4j Cypher Export, Knowledge Graph Operations (Neo4j), Neo4j Docker Compose Service, GraphProvider Interface, Neo4jProvider, NullGraphProvider (+1 more)

### Community 94 - "plugin_loader.py"
Cohesion: 0.23
Nodes (12): _default_scan_dir(), Path, Plugin discovery and loading. Scans a directory tree for plugin subdirectories…, Discover and load all plugins found in *scan_dir*. Returns only plugins that…, Return the platform-appropriate plugin scan directory. On Windows:…, Import and return the class named by ``module:ClassName``. Temporarily prepends…, Return a list of permission mismatches. A mismatch occurs when a permission is…, _resolve_entry_point() (+4 more)

### Community 95 - "DebounceHandler"
Cohesion: 0.27
Nodes (5): DebounceHandler, Index a single new file and invoke post_index_hook on success., Watchdog event handler with per-path debouncing. Consecutive events for the…, FileSystemEvent, FileSystemEventHandler

### Community 96 - "TestExpand"
Cohesion: 0.36
Nodes (3): _expand(), Return additional terms for tokens that match the expansion dictionaries.…, TestExpand

### Community 97 - "TestNormalise"
Cohesion: 0.36
Nodes (3): _normalise(), Lowercase, unicode-normalise (NFC), and collapse internal whitespace., TestNormalise

### Community 98 - "TestDebounceHandler"
Cohesion: 0.36
Nodes (3): _make_handler(), Create a DebounceHandler with a fresh non-running loop (timers only)., TestDebounceHandler

### Community 99 - "package.json"
Cohesion: 0.22
Nodes (8): name, pnpm, onlyBuiltDependencies, private, type, version, esbuild, @tauri-apps/cli

### Community 100 - "ConversationServiceProvider.tsx"
Cohesion: 0.15
Nodes (13): apimEndpoint, LLM_CONFIG, LLMConfig, LLMProviderKey, providerOverride, ContextEngineContext, ConversationIdContext, ConversationIdContextValue (+5 more)

### Community 101 - "NullProjectKnowledgeRepository.ts"
Cohesion: 0.47
Nodes (3): NullProjectKnowledgeRepository, Project, ProjectKnowledgeRepository

### Community 102 - "IndexingStatusPanel.tsx"
Cohesion: 0.19
Nodes (15): IndexingStatusPanel(), IndexingTaskCard(), IndexingTaskCardProps, PassRow(), PassRowProps, PassState, resolveStage(), StageId (+7 more)

### Community 103 - "orb.py"
Cohesion: 0.27
Nodes (10): orb_query(), OrbQueryRequest, OrbQueryResponse, OrbSourceItem, Any, BaseModel, post, Request (+2 more)

### Community 104 - "TestTokenise"
Cohesion: 0.39
Nodes (3): Split on whitespace and punctuation, keeping hyphenated compounds whole. Tokens…, _tokenise(), TestTokenise

### Community 105 - "TestRemoveStopWords"
Cohesion: 0.39
Nodes (3): Remove tokens that are in the stop-word list., _remove_stop_words(), TestRemoveStopWords

### Community 106 - "PluginManifest"
Cohesion: 0.22
Nodes (8): PluginManifest, Path, Plugin manifest schema and loader. Each plugin must include a ``manifest.json``…, Validated, immutable representation of a plugin's manifest.json., Resolved at load time; None until set by the loader., PluginRecord, SQLite-backed plugin registry. Persists installed plugin metadata and their…, A plugin row as returned from the registry.

### Community 107 - "TestLooksLikeTypo"
Cohesion: 0.43
Nodes (3): _looks_like_typo(), Return True when the token exhibits common typo patterns. Checks: 1. Repeated…, TestLooksLikeTypo

### Community 108 - "FileIndexer"
Cohesion: 0.06
Nodes (34): _collect_files(), FileIndexer, _is_cloud_stub(), Path, Walk root recursively, skipping any directory in EXCLUDED_DIRS. Using os.walk…, Return True if the file is a OneDrive cloud-only placeholder. On non-Windows…, Recursively indexes text files in a workspace directory. For each file that is…, Return False if resolved is inside a blocked OS-critical directory. (+26 more)

### Community 110 - "FastAPI"
Cohesion: 0.24
Nodes (9): create_embedding(), EmbedRequest, EmbedResponse, BaseModel, field_validator, post, Embeddings router — POST /embeddings., Generate a BGE-M3 embedding vector for the supplied text. Returns a… (+1 more)

### Community 111 - "database.py"
Cohesion: 0.17
Nodes (18): _apply_migrations(), close_db(), _db_path(), _find_migrations_dir(), lifespan_db(), _migrations_dir(), open_db(), Connection (+10 more)

### Community 112 - "score_benchmark.py"
Cohesion: 0.29
Nodes (9): build_scorecard(), _folder_name(), load_recommendations(), Benchmark scorecard updater for the file-organisation pipeline. Reads…, Return the most-recent recommendation per file stem, pending-first. Scoring…, Return the basename of a path, or '' if None., Return (points, note) for a single recommendation result., score_result() (+1 more)

### Community 113 - "main"
Cohesion: 0.36
Nodes (7): main(), QueryTest, Run the search pipeline and return (response_text, sources)., Return (source_pts, content_pts, notes) for a test case., A single query test case. Scoring (per test, max 4 pts): source_pts: 2 if any…, run_query(), score_test()

### Community 114 - "generate_search_pipeline_pdf.py"
Cohesion: 0.48
Nodes (6): build_pdf(), build_styles(), code_block(), _content_page(), _cover_page_bg(), Generate a well-formatted PDF describing the Enterprise AI Companion search…

### Community 115 - "Capability Layer"
Cohesion: 0.33
Nodes (6): Capability-Based Organization, Clean Architecture Principle, Capability Layer, Domain Layer, External Systems, Infrastructure Layer

### Community 116 - "Benchmark Scorecard — File Organisation"
Cohesion: 0.22
Nodes (8): Benchmark Scorecard — File Organisation, Category 1 — Obvious Matches (scored 10 / 10), Category 2 — Semantic Matches (scored 6 / 10), Category 3 — Ambiguous Matches (scored 10 / 10), Category 4 — Wrong-Project Matches (scored 7 / 8), Category 5 — Unrelated Files (scored 6 / 6), Category 6 — Duplicate / Updated Versions (scored 7 / 10), Running Total

### Community 117 - "Python Sidecar (FastAPI)"
Cohesion: 0.33
Nodes (6): BGE-M3 Embedding Service, ConversationRepository, IPCClient, Python Sidecar (FastAPI), ConversationMemoryService, Home Page Dashboard

### Community 118 - "Presentation Layer"
Cohesion: 0.40
Nodes (5): Architecture Decision Records (ADRs), Layered Architecture, Application Layer, Presentation Layer, Architecture Documentation Suite

### Community 119 - "File Indexing Capability"
Cohesion: 0.40
Nodes (5): File Indexing Capability, FileConnector Interface, FileIndexer, LocalFileConnector, OneDriveConnector

### Community 120 - "HomePage.tsx"
Cohesion: 0.08
Nodes (25): AuthGuard(), AuthGuardProps, GlassPrompt(), GlassPromptProps, OVERLAY_VARIANTS, PANEL_VARIANTS, ACCENT_CLASSES, formatValue() (+17 more)

### Community 121 - "lint-staged"
Cohesion: 0.50
Nodes (5): lint-staged, src/**/*.{json,css,md}, src/**/*.{ts,tsx}, eslint --fix, prettier --write

### Community 122 - "Enterprise AI Companion App Icon (main)"
Cohesion: 0.40
Nodes (5): Tauri Framework Logo, App Icon 128x128, App Icon 32x32, Enterprise AI Companion App Icon (main), App Store Logo

### Community 123 - "WorkspacePage.tsx"
Cohesion: 0.28
Nodes (11): applyFiltersAndSort(), DocumentBrowser(), folderName(), formatTimestamp(), IndexingErrorsTab(), WorkspaceExplorer(), useWorkspace(), STATIC_TABS (+3 more)

### Community 124 - ".process"
Cohesion: 0.50
Nodes (3): ProcessedQuery, Run the full preprocessing pipeline on raw_query. Args: raw_query: Unmodified…, Result of running a raw query through the preprocessing pipeline. Attributes:…

### Community 125 - "BFS Graph Traversal Query"
Cohesion: 0.67
Nodes (3): BFS Graph Traversal Query, Save Result Feedback Loop, Query Vocabulary Expansion

### Community 128 - "Settings Page"
Cohesion: 0.67
Nodes (3): BackupService, Settings Page, Settings Service (Frontend)

### Community 133 - "devDependencies"
Cohesion: 0.22
Nodes (9): eslint, eslint-plugin-prettier, devDependencies, eslint, eslint-plugin-prettier, typescript, @vitejs/plugin-react, typescript (+1 more)

### Community 134 - "OrbLayer.tsx"
Cohesion: 0.18
Nodes (9): useDesktopPresence(), useOrbDrag(), GlassPromptContainer(), OrbLayer(), OrbControllerContext, OrbControllerProvider(), GlassPromptStore, useGlassPromptStore (+1 more)

### Community 146 - "OrganiseDashboard.tsx"
Cohesion: 0.22
Nodes (8): OrganiseDashboard(), OrganiseDashboardProps, StatTileProps, RecommendationRow(), RecommendationRowProps, PendingRecommendation, CONFIDENT_THRESHOLD, LOW_CONFIDENCE_THRESHOLD

### Community 153 - ".log"
Cohesion: 0.33
Nodes (5): Any, Return a copy of details with sensitive values replaced by '<redacted>'., Record a single audit event. Args: event_type: Dot-namespaced verb, e.g.…, Return the most recent audit events, newest first., _scrub()

### Community 154 - "Volvo Group Abbreviations Reference"
Cohesion: 0.18
Nodes (10): Agile & SAFe, Engineering & Product Development, Enterprise Systems & Data, IT & DevOps, ITSM & Service Management, Project & Governance, Security & Compliance, Supply Chain & Quality (+2 more)

### Community 156 - "HybridRerankAdapter"
Cohesion: 0.23
Nodes (11): HybridRerankAdapter, Satisfies RerankPort using HybridSearchOrchestrator. Owns both the chunk-text…, Return mean RRF score of top-5 results from hybrid search scoped to…, AuditTest, _cleanup(), main(), PlacementTest, Return (pts 0/1/2, verdict) for a placement test case. (+3 more)

### Community 193 - "benchmark_downloads.py"
Cohesion: 0.48
Nodes (6): _dismiss_recommendation(), main(), _open_db(), _poll_for_recommendation(), Poll until a pending recommendation exists for downloads_path or timeout.…, _score_result()

### Community 194 - "MainContent.tsx"
Cohesion: 0.09
Nodes (29): PlaceholderPage(), PlaceholderPageProps, MainContent(), PAGE_MAP, PAGE_TRANSITION, PageModule, TopBar(), TopBarProps (+21 more)

### Community 195 - "test_conversation_repository.py"
Cohesion: 0.33
Nodes (6): db(), Connection, fixture, Unit tests for ConversationRepository using an in-memory SQLite database., In-memory SQLite database with schema applied, closed after each test., repo()

### Community 196 - "IPCClient"
Cohesion: 0.20
Nodes (8): useEmbedding(), UseEmbeddingResult, IPCClient, waitForSidecar(), mockInvoke, mockListen, FAKE_VECTOR, mockGenerateEmbedding

### Community 197 - "BackupSettings.tsx"
Cohesion: 0.31
Nodes (6): BackupSettings(), formatBytes(), formatDate(), BackupResult, BackupSummary, SettingsService

### Community 198 - "Passive Background Suggester (Phase 10 deferral)"
Cohesion: 0.33
Nodes (5): Deferred Features, Passive Background Suggester (Phase 10 deferral), Preferred future implementation, What was deferred, Why it was deferred

### Community 199 - "Volvo IT Terminology Glossary"
Cohesion: 0.20
Nodes (9): Agile Framework Terms, Backlog & Work Items, Ceremonies & Events, Collaboration & Tools, DevOps & Delivery, Metrics & Tracking, Project Planning & Governance, Roles (+1 more)

### Community 200 - "APIMProvider.ts"
Cohesion: 0.19
Nodes (14): APIMChatCompletion, APIMRequestBody, APIMStreamDelta, RETRYABLE_STATUS_CODES, ChatMessage, LLMRequestOptions, LLMStreamChunk, ParsedToolCall (+6 more)

### Community 201 - "get_db"
Cohesion: 0.50
Nodes (4): get_db(), Connection, Request, Extract the shared database connection from app state.

### Community 204 - "_is_excluded"
Cohesion: 0.33
Nodes (3): _is_excluded(), Return True if any segment of path is in EXCLUDED_DIRS., TestIsExcluded

### Community 205 - "IndexedDocument"
Cohesion: 0.20
Nodes (12): DocumentRow(), DocumentRowProps, EXT_ICONS, formatDate(), formatSize(), getExtension(), getFileName(), fileName() (+4 more)

### Community 206 - "RecentFilesList.tsx"
Cohesion: 0.48
Nodes (6): fileName(), formatDate(), OpenButton(), RecentFilesList(), RecentFilesListProps, RecentFile

### Community 218 - "limit_request_body"
Cohesion: 0.28
Nodes (7): health(), limit_request_body(), get, Reject requests with a Content-Length header exceeding 10 MiB., Liveness probe used by the Tauri IPC health_check command., middleware, StarletteRequest

### Community 219 - "manifest.json"
Cohesion: 0.25
Nodes (7): backup_id, created_at, notes, qdrant_collections, sqlite_size_bytes, status, document_chunks

## Knowledge Gaps
- **493 isolated node(s):** `enterprise-ai-companion`, `backup_id`, `created_at`, `sqlite_size_bytes`, `document_chunks` (+488 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **81 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AzureTokenData` connect `auth.rs` to `lib.rs`, `file_indexer.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `GraphProvider` connect `GraphProvider` to `TestEntityExtractor`, `file_indexer.py`, `GraphQueryService`, `KnowledgeGraphService`, `Entity`, `FileIndexer`, `context_assembler.py`, `Neo4jProvider`, `SQLiteGraphProvider`, `NullGraphProvider`, `TestCanonicalName`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `FileIndexer` connect `FileIndexer` to `GraphProvider`, `file_indexer.py`, `app.py`, `KnowledgeGraphService`, `.__init__`, `TextChunker`, `GraphStateRepository`, `PluginManager`, `database.py`, `NullGraphProvider`, `DocumentRepository`, `WatcherService`, `indexing.py`, `EmbeddingService`, `HybridRerankAdapter`, `ChunkRepository`, `DebounceHandler`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `EmbeddingService` (e.g. with `AzureTokenMiddleware` and `TokenVerificationMiddleware`) actually correct?**
  _`EmbeddingService` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `NullGraphProvider` (e.g. with `AzureTokenMiddleware` and `TokenVerificationMiddleware`) actually correct?**
  _`NullGraphProvider` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `FileIndexer` (e.g. with `AzureTokenMiddleware` and `TokenVerificationMiddleware`) actually correct?**
  _`FileIndexer` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `enterprise-ai-companion`, `backup_id`, `created_at` to the rest of the system?**
  _493 weakly-connected nodes found - possible documentation gaps or missing edges._