# Graph Report - Enterprise-AI-Companion  (2026-08-11)

## Corpus Check
- 358 files · ~175,602 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2896 nodes · 6036 edges · 219 communities (150 shown, 69 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 598 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2bec113f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- lib.rs
- plugin_manager.py
- Entity
- ChunkRepository
- BackupService
- graph.py
- settingsStore.ts
- IPCClient.ts
- EntityType
- Technology Stack
- MessageBubble.tsx
- utils.ts
- compilerOptions
- MainContent.tsx
- FileIndexer
- context_assembler.py
- ._index_file
- OrbController.ts
- HybridSearchOrchestrator
- dependencies
- SearchPage.tsx
- RelationshipType
- NullGraphProvider
- DocumentRepository
- workspace.ts
- conversations.py
- file_indexer.py
- EmbeddingService
- HybridSearchResult
- Implementation Documentation Overview
- Phase-09-File-Organisation-New-Files.md
- TestCanonicalName
- HybridSearchOrchestrator
- Search Pipeline Architecture
- tauri.conf.json
- AbbreviationExtractor
- GraphCanvas.tsx
- KeywordSearchProvider
- Phase-08-Orb-Native-Shell.md
- SearchResult
- ConversationRepository
- OrbAnimationEngine.tsx
- QueryPreprocessor
- OrbLayer.tsx
- TextChunker
- _make_watcher
- @eslint/js
- watcher.py
- GlassPromptIntegration.test.tsx
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
- APIMProvider.ts
- Graphify Knowledge Graph Tool
- GraphStateRepository
- KnowledgeGraphService
- _escape_fts5_query
- TestEntityExtractor
- stats.py
- app.py
- qdrant_provider.py
- HomePage.tsx
- cn
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
- get_config
- Engineering Specification (CLAUDE.md)
- DebounceHandler
- default.json
- scripts
- ConversationServiceProvider.tsx
- PluginRegistry
- .send
- compilerOptions
- server.py
- _detect_intent
- TestEmbeddingsEndpoint
- Neo4j Graph Database
- plugin_loader.py
- TestIsExcluded
- TestExpand
- TestNormalise
- TestDebounceHandler
- package.json
- LLMProvider
- NullProjectKnowledgeRepository.ts
- WorkspacePage.tsx
- IndexingErrorRepository
- TestTokenise
- TestRemoveStopWords
- PluginManifest
- TestLooksLikeTypo
- OrbShell.tsx
- test_package.py
- TraversalEngine
- database.py
- services/orb/index.ts
- IPCClient
- generate_search_pipeline_pdf.py
- Capability Layer
- GraphQueryService
- Python Sidecar (FastAPI)
- Presentation Layer
- File Indexing Capability
- StatusBar.tsx
- lint-staged
- Enterprise AI Companion App Icon (main)
- LivingOrb.tsx
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
- GlassPromptContainer.test.tsx
- autoprefixer
- eslint-plugin-react-hooks
- husky
- jiti
- lint-staged
- prettier
- @radix-ui/react-dialog
- @radix-ui/react-dropdown-menu
- @radix-ui/react-label
- @radix-ui/react-separator
- @radix-ui/react-slot
- @radix-ui/react-switch
- @radix-ui/react-toast
- @radix-ui/react-tooltip
- @tauri-apps/cli
- @testing-library/react
- @types/node
- @types/react
- clsx
- vite
- vite-tsconfig-paths
- eslint-plugin-react
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
- eslint-plugin-react-refresh
- framer-motion
- lucide-react
- react
- react-markdown
- @tauri-apps/api
- @tauri-apps/plugin-http
- zustand
- jsdom
- @radix-ui/react-avatar
- @radix-ui/react-scroll-area
- @testing-library/jest-dom
- @types/d3-force
- @types/react-dom
- typescript-eslint
- DesktopPresenceService
- embeddings.py
- test_file_indexer.py
- .cancel_all
- DocumentRow.tsx
- useDashboard.ts
- ._reachable_ids
- TestWatcherServiceFolders
- graph_state_repository.py
- .upsert_entity
- eslint-plugin-prettier

## God Nodes (most connected - your core abstractions)
1. `cn()` - 123 edges
2. `NullGraphProvider` - 61 edges
3. `EmbeddingService` - 54 edges
4. `FileIndexer` - 54 edges
5. `Entity` - 50 edges
6. `Relationship` - 48 edges
7. `GraphProvider` - 47 edges
8. `AppState` - 46 edges
9. `ConversationRepository` - 44 edges
10. `GraphQueryService` - 42 edges

## Surprising Connections (you probably didn't know these)
- `AI Agent UI Design Mockup` --conceptually_related_to--> `Search Pipeline Architecture`  [INFERRED]
  UI-Design-Mockup/AI_Agent.png → docs/Search-Pipeline-Architecture.pdf
- `AI Agent UI Design Mockup` --conceptually_related_to--> `useConversation.ts`  [INFERRED]
  UI-Design-Mockup/AI_Agent.png → docs/Search-Pipeline-Architecture.pdf
- `FileIndexer` --semantically_similar_to--> `File Indexing Capability`  [INFERRED] [semantically similar]
  docs/BACKLOG.md → backend/README.md
- `Engineering Specification (CLAUDE.md)` --conceptually_related_to--> `Architecture Documentation Suite`  [INFERRED]
  .claude/CLAUDE.md → docs/architecture/README.md
- `Knowledge Graph Operations (Neo4j)` --references--> `Neo4j Graph Database`  [INFERRED]
  backend/README.md → .claude/CLAUDE.md

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

## Communities (219 total, 69 thin omitted)

### Community 0 - "lib.rs"
Cohesion: 0.09
Nodes (105): App, AppHandle, Arc, Child, Client, accept_recommendation(), add_watched_folder(), AddFolderRequest (+97 more)

### Community 1 - "plugin_manager.py"
Cohesion: 0.16
Nodes (14): FileProcessorPlugin, ABC, Abstract base classes defining the extension points available to plugins. A…, Extract plain text from files of a custom type. Registered plugins are…, Return lowercase dot-prefixed extensions, e.g. ``frozenset({".abc"})``., Transform extracted text before it is chunked and embedded. Plugins in this…, Return the (possibly modified) text. *file_path* is provided as context only;…, Augment hybrid search results after the core ranking step. NOTE: Wiring into… (+6 more)

### Community 2 - "Entity"
Cohesion: 0.06
Nodes (38): Entity, GraphContext, Context retrieved from the knowledge graph for a given query entity., Relationship, GraphProvider, ABC, Abstract interface for the knowledge graph provider. Business logic depends on…, Defines the contract for all graph storage backends. (+30 more)

### Community 3 - "ChunkRepository"
Cohesion: 0.11
Nodes (22): bulk_delete_documents(), BulkDeleteRequest, delete_document(), DocumentResponse, list_documents(), BaseModel, delete, get (+14 more)

### Community 4 - "BackupService"
Cohesion: 0.05
Nodes (39): BackupResultResponse, BackupSummaryResponse, create_backup(), CreateBackupRequest, delete_backup(), DeleteBackupResponse, _get_service(), list_backups() (+31 more)

### Community 5 - "graph.py"
Cohesion: 0.15
Nodes (32): ConnectedDocumentsResponse, _entity_to_response(), EntityResponse, EntitySearchResponse, find_path(), get_connected_documents(), get_entity_context(), get_graph_visualization() (+24 more)

### Community 6 - "settingsStore.ts"
Cohesion: 0.10
Nodes (26): AssistantHeader(), AssistantHeaderProps, resolveStatus(), AssistantStatus(), AssistantStatusProps, STATUS_CONFIG, StatusKind, MODES (+18 more)

### Community 7 - "IPCClient.ts"
Cohesion: 0.03
Nodes (19): ConversationMemory, ConversationSummary, EmbedResponse, GraphContextResponse, GraphEntityItem, GraphHealthResponse, GraphRelationshipItem, HealthResponse (+11 more)

### Community 8 - "EntityType"
Cohesion: 0.10
Nodes (23): Knowledge graph enrichment service. Runs after entity and relationship…, _coerce_entity_type(), Extracts named entities from text using a structured LLM call. Replaces the…, EntityType, ExtractedRelationship, Enum, str, Shared domain models for the knowledge graph capability. (+15 more)

### Community 9 - "Technology Stack"
Cohesion: 0.08
Nodes (45): Capability Model, AI Services Capability, Automation Capability, Conversation Capability, File Intelligence Capability, Knowledge Management Capability, Search & Retrieval Capability, Settings & Configuration Capability (+37 more)

### Community 10 - "MessageBubble.tsx"
Cohesion: 0.08
Nodes (34): AssistantAvatar(), AssistantAvatarProps, SIZE_CLASSES, CitationChip(), CitationChipProps, ConversationView(), ConversationViewProps, FilePathChip() (+26 more)

### Community 11 - "utils.ts"
Cohesion: 0.11
Nodes (22): AssistantFooter(), AssistantFooterProps, AssistantWidget(), AssistantWidgetProps, PromptComposer(), PromptComposerProps, PromptInput(), PromptInputProps (+14 more)

### Community 12 - "compilerOptions"
Cohesion: 0.05
Nodes (39): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+31 more)

### Community 13 - "MainContent.tsx"
Cohesion: 0.08
Nodes (35): Logo(), LogoProps, PlaceholderPage(), PlaceholderPageProps, SuggestedQueries(), SuggestedQueriesProps, MainContent(), PAGE_MAP (+27 more)

### Community 14 - "FileIndexer"
Cohesion: 0.19
Nodes (8): AbstractEventLoop, FileIndexer, Recursively indexes text files in a workspace directory. For each file that is…, Connection, Path, Unit tests for the _extract_text dispatcher., TestExtractText, TestIndexWorkspace

### Community 15 - "context_assembler.py"
Cohesion: 0.09
Nodes (28): ContextAssembler, ContextChunk, ContextPayload, Connection, QdrantClient, Context assembly service for the AI retrieval pipeline. Wraps the hybrid search…, Retrieve and assemble context chunks for the given query. Pipeline: 1. Hybrid…, Supplement vector-retrieved chunks with graph-neighbour chunks. For each token… (+20 more)

### Community 16 - "._index_file"
Cohesion: 0.13
Nodes (12): _collect_files(), _is_cloud_stub(), Path, Return True if the file is a OneDrive cloud-only placeholder. On non-Windows…, Return False if resolved is inside a blocked OS-critical directory., Index all supported files under workspace_path. Returns a summary. progress_cb…, Extract plain text from a file based on its extension. Enabled…, Index a single file. Returns True if indexed, False if unchanged. (+4 more)

### Community 17 - "OrbController.ts"
Cohesion: 0.15
Nodes (5): ORB_OVERLAY_ID, OrbControllerState, OrbStateListener, Overlay, OverlayRegistry

### Community 18 - "HybridSearchOrchestrator"
Cohesion: 0.15
Nodes (27): _get_db(), hybrid_search(), HybridSearchRequest, HybridSearchResponse, HybridSearchResultItem, keyword_search(), KeywordSearchRequest, KeywordSearchResponse (+19 more)

### Community 19 - "dependencies"
Cohesion: 0.12
Nodes (17): class-variance-authority, d3-force, dependencies, class-variance-authority, d3-force, postcss, react-dom, remark-gfm (+9 more)

### Community 20 - "SearchPage.tsx"
Cohesion: 0.13
Nodes (20): EmptySearchState(), EmptySearchStateProps, SearchFilters(), SearchFiltersProps, TOP_K_OPTIONS, SearchInput(), SearchInputProps, MODES (+12 more)

### Community 21 - "RelationshipType"
Cohesion: 0.10
Nodes (23): RelationshipType, Connection, Remove all entities (and cascade-delete their relationships) for a document., Case-insensitive substring search over entity names., Return document IDs reachable within 2 hops from *entity_name*. Uses a…, Knowledge graph backed by SQLite. Uses the graph_entities and…, No-op: tables and indexes are created by migration 008., No-op: connection lifecycle is managed by the application. (+15 more)

### Community 22 - "NullGraphProvider"
Cohesion: 0.13
Nodes (4): NullGraphProvider, provider(), fixture, TestNullGraphProvider

### Community 23 - "DocumentRepository"
Cohesion: 0.12
Nodes (15): DocumentRepository, IndexedDocument, Connection, Repository for indexed document metadata stored in SQLite., db(), _make_doc(), Connection, fixture (+7 more)

### Community 24 - "workspace.ts"
Cohesion: 0.11
Nodes (22): PendingDelete, DocumentFilters(), DocumentFiltersProps, EXTENSION_OPTIONS, SORT_OPTIONS, DocumentRowProps, FolderRow(), FolderRowProps (+14 more)

### Community 25 - "conversations.py"
Cohesion: 0.10
Nodes (28): ConversationMemoryResponse, ConversationResponse, ConversationSummaryResponse, get_conversation_memory(), get_db(), list_conversations(), load_conversation(), MessageResponse (+20 more)

### Community 26 - "file_indexer.py"
Cohesion: 0.10
Nodes (29): cancel_indexing(), clear_indexing_errors(), get_indexing_status(), IndexingErrorResponse, IndexingStatusResponse, list_indexing_errors(), Any, BaseModel (+21 more)

### Community 27 - "EmbeddingService"
Cohesion: 0.09
Nodes (15): EmbeddingService, Generates dense text embeddings using bge-small-en-v1.5 locally via ONNX…, Return a single embedding vector for the given text. Args: text: The input…, Return embedding vectors for a list of texts. Args: texts: A non-empty list of…, Connection, QdrantClient, Connection, QdrantClient (+7 more)

### Community 28 - "HybridSearchResult"
Cohesion: 0.19
Nodes (7): HybridSearchResult, A single result from the hybrid search pipeline. The rrf_score is the combined…, _make_client(), TestClient, Tests for the hybrid search orchestrator and /search/hybrid endpoint. Covers…, Return a TestClient with mocked app.state attributes., TestHybridSearchEndpoint

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

### Community 34 - "tauri.conf.json"
Cohesion: 0.08
Nodes (23): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+15 more)

### Community 35 - "AbbreviationExtractor"
Cohesion: 0.09
Nodes (17): AbbreviationRepository, Connection, Repository for persisting and querying discovered abbreviations. Abbreviation…, Async repository for the ``abbreviations`` table. Args: conn: An open…, Persist a batch of abbreviation matches for a single document. Uses ``INSERT OR…, Remove all abbreviation rows for the given document. Called before re-indexing…, Load all discovered abbreviations across every document. Returns a mapping…, AbbreviationExtractor (+9 more)

### Community 36 - "GraphCanvas.tsx"
Cohesion: 0.14
Nodes (21): confidenceColor(), confidenceLabel(), EntityCard(), EntityCardProps, drawArrow(), drawFrame(), ENTITY_COLORS, entityColor() (+13 more)

### Community 37 - "KeywordSearchProvider"
Cohesion: 0.15
Nodes (12): KeywordSearchProvider, Connection, Full-text keyword search over indexed document chunks using SQLite FTS5. The…, db(), asyncio, Connection, fixture, Tests for KeywordSearchProvider. (+4 more)

### Community 38 - "Phase-08-Orb-Native-Shell.md"
Cohesion: 0.10
Nodes (19): Animation States, Architecture, Completion Criteria, Deliverables, Dependencies, Design Decisions, Interaction Model, Modified Files (+11 more)

### Community 39 - "SearchResult"
Cohesion: 0.17
Nodes (7): Hybrid search orchestrator combining keyword and semantic search. Uses…, Execute hybrid search and return merged results. Args: query: Preprocessed…, Keyword search provider backed by SQLite FTS5., Look up the file_path for a document_id from SQLite., Return top_k chunks most semantically similar to query. Args: query: Natural-…, Shared data models for the search capability., SearchResult

### Community 40 - "ConversationRepository"
Cohesion: 0.11
Nodes (14): ConversationRepository, Atomically increment turn_count and return the new value., Persist a compressed summary for the conversation., Async repository for conversation and message persistence., db(), Connection, fixture, Unit tests for ConversationRepository using an in-memory SQLite database. (+6 more)

### Community 41 - "OrbAnimationEngine.tsx"
Cohesion: 0.17
Nodes (21): OrbIconProps, ORB_BORDER_COLOR, ORB_GRADIENT_FROM, ORB_GRADIENT_MID, ORB_GRADIENT_TO, ORB_HIGHLIGHT_COLOR, ORB_HIGHLIGHT_SIZE, ORB_RADIUS (+13 more)

### Community 42 - "QueryPreprocessor"
Cohesion: 0.17
Nodes (6): QueryPreprocessor, QueryPreprocessorConfig, Transforms a raw user query into a structured ProcessedQuery. Designed to be…, Replace the dynamic expansion set with entries from discovered abbreviations.…, Feature flags for the preprocessing pipeline., TestQueryPreprocessor

### Community 43 - "OrbLayer.tsx"
Cohesion: 0.19
Nodes (13): useOrbController(), DragOrigin, useOrbDrag(), UseOrbDragOptions, UseOrbDragResult, useOrbPosition(), OrbLayer(), clamp() (+5 more)

### Community 44 - "TextChunker"
Cohesion: 0.15
Nodes (7): Splits plain text into overlapping character-based chunks for embedding., Splits text into overlapping chunks, preferring sentence boundaries. Args:…, Return a list of (content, char_start, char_end) tuples. Chunks are at most…, Return the character position of the last sentence break in text, or 0., TextChunker, Unit tests for TextChunker., TestChunker

### Community 45 - "_make_watcher"
Cohesion: 0.19
Nodes (10): _client_with_watcher(), _make_watcher(), TestClient, WatchedFolder, Build a minimal WatcherService mock for injection into app.state., Return a TestClient that has watcher injected after lifespan starts., TestAddFolder, TestListFolders (+2 more)

### Community 47 - "watcher.py"
Cohesion: 0.16
Nodes (18): add_watched_folder(), AddFolderRequest, get_watcher_status(), list_watched_folders(), BaseModel, delete, get, post (+10 more)

### Community 48 - "GlassPromptIntegration.test.tsx"
Cohesion: 0.22
Nodes (3): ConversationServiceContext, ConversationService, ConversationTurn

### Community 49 - "OrbController"
Cohesion: 0.18
Nodes (3): OrbController, makeControllableProvider(), renderIntegration()

### Community 50 - "OrbState"
Cohesion: 0.19
Nodes (6): OrbAnimationController, OrbAnimationDriver, OrbState, OrbStateListener, OrbStateMachine, TRANSITIONS

### Community 51 - "Neo4jProvider"
Cohesion: 0.08
Nodes (17): _auth(), Neo4jProvider, _node_to_entity(), Any, Neo4j-backed knowledge graph provider. Uses the official Neo4j Python async…, Create or update a directed relationship between two entity nodes. Both nodes…, Return the named entity plus its neighbourhood up to `depth` hops. Depth is…, Return ``{"nodes": [...], "edges": [...]}`` for the graph UI. When… (+9 more)

### Community 52 - "_mock_db_app"
Cohesion: 0.13
Nodes (13): ConversationSummary, Message, Return all messages for a conversation, oldest first., Return up to `limit` messages, oldest first, for summarisation., Return all conversations, most recent first, with their message count., _make_message(), _mock_db_app(), Tests for the conversations FastAPI endpoints using an in-memory database. (+5 more)

### Community 53 - "_make_result"
Cohesion: 0.16
Nodes (9): Merge two ranked lists using Reciprocal Rank Fusion. Each chunk accumulates an…, _rrf_merge(), _make_result(), asyncio, Verify the score for a chunk that appears at rank 1 in one list only., A chunk_id appearing in both lists should produce exactly one result., semantic_weight=0 should suppress semantic contribution., TestHybridSearchOrchestrator (+1 more)

### Community 54 - "App.tsx"
Cohesion: 0.17
Nodes (14): useDesktopPresence(), DesktopPresenceContext, DesktopPresenceProvider(), DesktopPresenceProviderProps, LayoutProvider(), LayoutProviderProps, OrbControllerProvider(), applyThemeToDocument() (+6 more)

### Community 55 - "retrieval/index.ts"
Cohesion: 0.29
Nodes (9): LocalFileConnector, OneDriveConnector, NullRetrievalBroker, DocumentFragment, RetrievalBroker, RetrievalQuery, RetrievalResult, ANY_QUERY (+1 more)

### Community 56 - "conversation_repository.py"
Cohesion: 0.22
Nodes (7): ConversationMemoryState, Conversation persistence repository. Provides async CRUD operations over the…, Persist a message, creating the parent conversation if needed., Return the turn_count and summary for a conversation. Creates the conversation…, Memory state for a single conversation, read from the conversations table., Return the conversation id, creating the row if it does not exist., _utc_now()

### Community 57 - "WatcherService"
Cohesion: 0.18
Nodes (9): Manages the watchdog Observer and the set of watched folders. Persists the…, Load persisted folders and start the watchdog Observer. Safe to call from…, Async start path — used when start() is called from inside the event loop., Register a new folder for watching. Triggers an immediate initial index., Persist a folder as watched and start the filesystem watch. Unlike add_folder,…, Return all registered watched folders., A folder registered for automatic background indexing., WatchedFolder (+1 more)

### Community 58 - "components.json"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 59 - "APIMProvider.ts"
Cohesion: 0.14
Nodes (9): APIMChatCompletion, APIMChatMessage, APIMError, APIMRequestBody, APIMStreamDelta, RETRYABLE_STATUS_CODES, makeSSEStream(), mockSSEResponse() (+1 more)

### Community 60 - "Graphify Knowledge Graph Tool"
Cohesion: 0.12
Nodes (17): Graphify Add URL Ingestion, Graphify Watch Folder Auto-Rebuild, MCP Server Graph Export, Wiki Export (Agent-Crawlable), Extraction Subagent Prompt, Cross-Repo Graph Merge, CLAUDE.md Graphify Integration, Post-Commit Auto-Rebuild Hook (+9 more)

### Community 61 - "GraphStateRepository"
Cohesion: 0.19
Nodes (8): GraphStateRepository, Connection, SQLite-backed store for per-document graph build state., Insert or replace the graph state for document_id., Remove the graph state entry for document_id., Connection, Integration tests using an in-memory SQLite database., TestGraphStateRepository

### Community 62 - "KnowledgeGraphService"
Cohesion: 0.18
Nodes (7): KnowledgeGraphService, Orchestrates entity extraction and graph persistence for indexed documents.…, Extract entities/relationships from each chunk and persist to the graph. After…, Remove all graph nodes and relationships sourced from this document., fixture, service(), TestBuildFromChunks

### Community 63 - "_escape_fts5_query"
Cohesion: 0.17
Nodes (7): _escape_fts5_query(), _normalise_bm25(), Escape a raw user query for safe use in an FTS5 MATCH expression. Wraps each…, Convert a raw SQLite BM25 score (negative, unbounded) to (0, 1]. SQLite's…, Return up to *top_k* chunks matching *query* via full-text search. Args: query:…, TestEscapeFts5Query, TestNormaliseBm25

### Community 64 - "TestEntityExtractor"
Cohesion: 0.12
Nodes (12): EntityExtractor, _parse_json(), Any, Attempt to parse raw LLM output as JSON, stripping markdown fences., Extracts named entities from a text chunk via a structured LLM call. Usage:…, Return extracted entities from text. Returns [] on failure., ExtractedEntity, Raw entity extracted by the LLM before graph persistence. (+4 more)

### Community 65 - "stats.py"
Cohesion: 0.18
Nodes (15): DashboardStats, _get_stats(), get_suggested_queries(), BaseModel, Connection, get, post, Request (+7 more)

### Community 66 - "app.py"
Cohesion: 0.06
Nodes (28): _build_graph_provider(), health(), lifespan(), limit_request_body(), get, FastAPI application for the Enterprise AI Companion backend., Reject requests that lack the per-session IPC shared secret. The token is…, Reject requests with a Content-Length header exceeding 10 MiB. (+20 more)

### Community 67 - "qdrant_provider.py"
Cohesion: 0.16
Nodes (15): _pid_file_path(), Path, QdrantClient, _qdrant_data_dir(), QdrantProvider, Local Qdrant vector store provider for the Enterprise AI Companion. Uses…, Manages the lifecycle of a local Qdrant client and the document_chunks…, Open the local Qdrant store and ensure the collection exists with correct dims.… (+7 more)

### Community 68 - "HomePage.tsx"
Cohesion: 0.18
Nodes (12): fileName(), formatDate(), OpenButton(), RecentFilesList(), RecentFilesListProps, ACCENT_CLASSES, formatValue(), ICON_ACCENT_CLASSES (+4 more)

### Community 69 - "cn"
Cohesion: 0.11
Nodes (24): AttachmentButton(), AttachmentButtonProps, CONTEXT_ITEMS, ContextBar(), ContextBarProps, ContextItem, EdgeLabel(), EdgeLabelProps (+16 more)

### Community 70 - "useConversation.ts"
Cohesion: 0.29
Nodes (8): cosine(), heuristicRerank(), needsRetrieval(), ngramTf(), RankedCandidate, tokenise(), ContextEngineContext, RetrievedChunk

### Community 71 - "Phase-10-File-Organisation-Existing-Files.md"
Cohesion: 0.11
Nodes (18): Architecture, Completion Criteria, Deduplication, Deliverables, Dependencies, Design Decisions, Modified Files, New Backend Modules (+10 more)

### Community 72 - "test_file_watcher.py"
Cohesion: 0.28
Nodes (6): db(), mock_indexer(), fixture, Unit tests for WatcherService and DebounceHandler., TestWatcherServiceStart, watcher_service()

### Community 73 - "SettingsPage.tsx"
Cohesion: 0.07
Nodes (27): GlassPrompt(), GlassPromptProps, OVERLAY_VARIANTS, PANEL_VARIANTS, AIProviderSettings(), AIProviderSettingsProps, BackupSettings(), formatBytes() (+19 more)

### Community 74 - "ContextSnapshot"
Cohesion: 0.28
Nodes (4): ContextEngine, ContextSnapshot, NullContextEngine, WorkspaceContextEngine

### Community 75 - "NotificationService"
Cohesion: 0.23
Nodes (3): Notification, NotificationService, NullNotificationService

### Community 76 - "query_preprocessor.py"
Cohesion: 0.20
Nodes (9): _has_fuzzy_candidates(), Enum, str, Query preprocessing pipeline for the search subsystem. Each stage is…, Return True if any token looks like it might be a typo. Heuristics: - Token…, Broad classification of the user's search intent., SearchIntent, Unit tests for the query preprocessing pipeline. (+1 more)

### Community 77 - "APIMProvider"
Cohesion: 0.23
Nodes (3): APIMConfig, APIMProvider, LLMStreamChunk

### Community 78 - "plugins.py"
Cohesion: 0.26
Nodes (12): disable_plugin(), enable_plugin(), list_plugins(), PluginResponse, BaseModel, get, post, Request (+4 more)

### Community 79 - "PluginManager"
Cohesion: 0.13
Nodes (9): PluginManager, Toggle a plugin's enabled state in the database. NOTE: The change takes effect…, Manages the full plugin lifecycle: discovery, persistence, and access., Scan for plugins, register them, and return summary counts. Returns: A dict…, Return enabled plugins that implement ``FileProcessorPlugin``., Return enabled plugins that implement ``TextProcessorPlugin``., Return enabled plugins that implement ``SearchEnricherPlugin``., Return all registered plugins from the database. (+1 more)

### Community 80 - "_make_client"
Cohesion: 0.23
Nodes (6): _make_client(), TestClient, Tests for the /graph API endpoints using NullGraphProvider injected into…, Return a TestClient with NullGraphProvider pre-loaded into app.state., TestGetGraphEntity, TestGraphHealth

### Community 81 - "get_config"
Cohesion: 0.11
Nodes (24): orb_query(), OrbQueryRequest, OrbQueryResponse, Any, BaseModel, post, Request, Orb window API endpoints. Provides a lightweight single-turn query endpoint… (+16 more)

### Community 82 - "Engineering Specification (CLAUDE.md)"
Cohesion: 0.23
Nodes (12): AI Provider Abstraction Layer, BGE-M3 Embeddings, Engineering Specification (CLAUDE.md), Enterprise AI Companion, OpenAI GPT-5 Mini, PaddleOCR, Qdrant Vector Store, Tauri Desktop Framework (+4 more)

### Community 83 - "DebounceHandler"
Cohesion: 0.36
Nodes (4): DebounceHandler, Watchdog event handler with per-path debouncing. Consecutive events for the…, FileSystemEvent, FileSystemEventHandler

### Community 84 - "default.json"
Cohesion: 0.18
Nodes (10): description, identifier, permissions, $schema, windows, core:default, global-shortcut:allow-register, global-shortcut:allow-unregister (+2 more)

### Community 85 - "scripts"
Cohesion: 0.18
Nodes (11): scripts, build, dev, format, lint, lint:fix, preview, tauri (+3 more)

### Community 86 - "ConversationServiceProvider.tsx"
Cohesion: 0.17
Nodes (12): apimEndpoint, LLM_CONFIG, LLMConfig, LLMProviderKey, providerOverride, ConversationIdContext, ConversationIdContextValue, ConversationServiceProvider() (+4 more)

### Community 87 - "PluginRegistry"
Cohesion: 0.13
Nodes (9): Connection, Path, PluginRegistry, Connection, Return all registered plugins, ordered by display_name., Return True if the plugin exists and is enabled., Read/write access to the plugins table., Insert or update a plugin row from *manifest*. Preserves the existing… (+1 more)

### Community 89 - "compilerOptions"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, types, include (+2 more)

### Community 90 - "server.py"
Cohesion: 0.24
Nodes (8): find_free_port(), _load_env_file(), Uvicorn startup and shutdown for the Enterprise AI Companion backend., Load key=value pairs from backend/.env into os.environ (if the file exists).…, Bind to port 0 so the OS assigns a free port, then release and return it., Start uvicorn on the given port (or a free OS-assigned port)., run(), Entry point: python -m enterprise_ai_companion

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

### Community 95 - "TestIsExcluded"
Cohesion: 0.33
Nodes (3): _is_excluded(), Return True if any segment of path is in EXCLUDED_DIRS., TestIsExcluded

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

### Community 100 - "LLMProvider"
Cohesion: 0.29
Nodes (7): LLMProvider, LLMRequestOptions, MOCK_RESPONSE_TABLE, MockProvider, MockResponseEntry, resolveResponse(), sleep()

### Community 101 - "NullProjectKnowledgeRepository.ts"
Cohesion: 0.47
Nodes (3): NullProjectKnowledgeRepository, Project, ProjectKnowledgeRepository

### Community 102 - "WorkspacePage.tsx"
Cohesion: 0.21
Nodes (15): applyFiltersAndSort(), DocumentBrowser(), FolderList(), formatTimestamp(), IndexingErrorsTab(), IndexingStatusPanel(), IndexingTaskCard(), IndexingTaskCardProps (+7 more)

### Community 103 - "IndexingErrorRepository"
Cohesion: 0.24
Nodes (5): IndexingError, IndexingErrorRepository, Connection, Persistence layer for indexing errors., Persists per-file indexing failures to SQLite.

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

### Community 108 - "OrbShell.tsx"
Cohesion: 0.19
Nodes (12): App(), root, OrbSvgFilters(), OrbNotificationOverlay(), Recommendation, OrbQueryOverlay(), QueryState, OrbShell() (+4 more)

### Community 110 - "TraversalEngine"
Cohesion: 0.16
Nodes (7): GraphPath, Delegate to the provider — it already implements 2-hop traversal., A shortest path between two named entities., Implements path-finding and connected-component traversal. Detects the provider…, Find the shortest path between two named entities (max 6 hops). Returns:…, Return document IDs of all entities reachable from entity_name. Traverses the…, TraversalEngine

### Community 111 - "database.py"
Cohesion: 0.22
Nodes (15): _apply_migrations(), close_db(), _db_path(), _find_migrations_dir(), lifespan_db(), _migrations_dir(), open_db(), Connection (+7 more)

### Community 112 - "services/orb/index.ts"
Cohesion: 0.24
Nodes (14): ErrorOccurredEvent, HoverEnterEvent, HoverLeaveEvent, InputFinishedEvent, InputStartedEvent, NotificationReceivedEvent, OrbEvent, OrbEventType (+6 more)

### Community 113 - "IPCClient"
Cohesion: 0.14
Nodes (11): useEmbedding(), UseEmbeddingResult, BackupResult, BackupSummary, IPCClient, waitForSidecar(), SettingsService, mockInvoke (+3 more)

### Community 114 - "generate_search_pipeline_pdf.py"
Cohesion: 0.48
Nodes (6): build_pdf(), build_styles(), code_block(), _content_page(), _cover_page_bg(), Generate a well-formatted PDF describing the Enterprise AI Companion search…

### Community 115 - "Capability Layer"
Cohesion: 0.33
Nodes (6): Capability-Based Organization, Clean Architecture Principle, Capability Layer, Domain Layer, External Systems, Infrastructure Layer

### Community 116 - "GraphQueryService"
Cohesion: 0.13
Nodes (6): GraphQueryService, Substring entity name search, sorted by confidence descending. Args: query:…, Return all document IDs that contain the named entity (up to 2 hops). Used by…, Provides high-level graph queries, abstracting Cypher from callers. Backed by…, Return the named entity and its direct neighbourhood (depth 1). Returns None…, Return entity plus N-hop neighbours. Args: entity_name: Exact entity name.…

### Community 117 - "Python Sidecar (FastAPI)"
Cohesion: 0.33
Nodes (6): BGE-M3 Embedding Service, ConversationRepository, IPCClient, Python Sidecar (FastAPI), ConversationMemoryService, Home Page Dashboard

### Community 118 - "Presentation Layer"
Cohesion: 0.40
Nodes (5): Architecture Decision Records (ADRs), Layered Architecture, Application Layer, Presentation Layer, Architecture Documentation Suite

### Community 119 - "File Indexing Capability"
Cohesion: 0.40
Nodes (5): File Indexing Capability, FileConnector Interface, FileIndexer, LocalFileConnector, OneDriveConnector

### Community 120 - "StatusBar.tsx"
Cohesion: 0.18
Nodes (11): STATUS_CLASSES, STATUS_LABELS, StatusIndicator(), StatusIndicatorProps, StatusVariant, DEFAULT_STATUS, fetchServiceStatus(), ServiceStatus (+3 more)

### Community 121 - "lint-staged"
Cohesion: 0.50
Nodes (5): lint-staged, src/**/*.{json,css,md}, src/**/*.{ts,tsx}, eslint --fix, prettier --write

### Community 122 - "Enterprise AI Companion App Icon (main)"
Cohesion: 0.40
Nodes (5): Tauri Framework Logo, App Icon 128x128, App Icon 32x32, Enterprise AI Companion App Icon (main), App Store Logo

### Community 123 - "LivingOrb.tsx"
Cohesion: 0.29
Nodes (7): LivingOrb(), LivingOrbProps, OrbContainer(), OrbContainerProps, OrbIcon(), ORB_FOCUS_RING, ORB_SIZE

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
Nodes (9): eslint, eslint-config-prettier, devDependencies, eslint, eslint-config-prettier, typescript, @vitejs/plugin-react, typescript (+1 more)

### Community 134 - "GlassPromptContainer.test.tsx"
Cohesion: 0.31
Nodes (4): GlassPromptContainer(), OrbControllerContext, GlassPromptStore, useGlassPromptStore

### Community 209 - "embeddings.py"
Cohesion: 0.27
Nodes (8): create_embedding(), EmbedRequest, EmbedResponse, BaseModel, field_validator, post, Embeddings router — POST /embeddings., Generate a BGE-M3 embedding vector for the supplied text. Returns a…

### Community 210 - "test_file_indexer.py"
Cohesion: 0.27
Nodes (9): db(), indexer(), mock_embedding_service(), mock_qdrant(), Connection, fixture, Integration tests for FileIndexer using a temporary directory and in-memory…, Minimal Qdrant client mock — records upsert calls without real vector ops. (+1 more)

### Community 211 - ".cancel_all"
Cohesion: 0.29
Nodes (3): Cancel pending debounce timers — called when a watch is removed., Stop the Observer and cancel all pending debounce timers., Unregister a folder and stop watching it.

### Community 212 - "DocumentRow.tsx"
Cohesion: 0.48
Nodes (6): DocumentRow(), EXT_ICONS, formatDate(), formatSize(), getExtension(), getFileName()

### Community 213 - "useDashboard.ts"
Cohesion: 0.43
Nodes (6): CachedSuggestions, DashboardState, loadCachedSuggestions(), saveSuggestionsCache(), useDashboard(), DashboardStats

### Community 214 - "._reachable_ids"
Cohesion: 0.33
Nodes (3): Return ``{"nodes": [...], "edges": [...]}`` for the graph UI. When…, Return entity IDs reachable from *entity_name* within *depth* hops., Recursive CTE that expands *depth* hops from *root_id* in both directions.

### Community 216 - "graph_state_repository.py"
Cohesion: 0.40
Nodes (3): GraphState, Tracks the last successful knowledge graph build per document. Allows…, Return the stored graph state for document_id, or None if not found.

### Community 217 - ".upsert_entity"
Cohesion: 0.50
Nodes (3): _canonical(), Inline canonical-name helper (mirrors enrichment_service.canonical_name). Kept…, Insert or update an entity node. Uses INSERT OR REPLACE so re-indexing the same…

## Knowledge Gaps
- **428 isolated node(s):** `enterprise-ai-companion`, `$schema`, `style`, `rsc`, `tsx` (+423 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **69 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NullGraphProvider` connect `NullGraphProvider` to `TestEntityExtractor`, `Entity`, `app.py`, `ChunkRepository`, `AbbreviationExtractor`, `EntityType`, `FileIndexer`, `context_assembler.py`, `TraversalEngine`, `_make_client`, `GraphQueryService`, `file_indexer.py`, `GraphStateRepository`, `KnowledgeGraphService`, `TestCanonicalName`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `FileIndexer` connect `FileIndexer` to `Entity`, `app.py`, `AbbreviationExtractor`, `ChunkRepository`, `IndexingErrorRepository`, `TextChunker`, `PluginManager`, `._index_file`, `test_file_indexer.py`, `DebounceHandler`, `NullGraphProvider`, `DocumentRepository`, `WatcherService`, `file_indexer.py`, `EmbeddingService`, `GraphStateRepository`, `KnowledgeGraphService`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `WatcherService` connect `WatcherService` to `app.py`, `TestDebounceHandler`, `test_file_watcher.py`, `FileIndexer`, `.cancel_all`, `TestWatcherServiceFolders`, `TestIsExcluded`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `NullGraphProvider` (e.g. with `TokenVerificationMiddleware` and `BulkDeleteRequest`) actually correct?**
  _`NullGraphProvider` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `EmbeddingService` (e.g. with `TokenVerificationMiddleware` and `EmbedRequest`) actually correct?**
  _`EmbeddingService` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `FileIndexer` (e.g. with `TokenVerificationMiddleware` and `IndexingErrorResponse`) actually correct?**
  _`FileIndexer` has 24 INFERRED edges - model-reasoned connections that need verification._
- **What connects `enterprise-ai-companion`, `$schema`, `style` to the rest of the system?**
  _428 weakly-connected nodes found - possible documentation gaps or missing edges._