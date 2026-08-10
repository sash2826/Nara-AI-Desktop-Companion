# Graph Report - .  (2026-08-10)

## Corpus Check
- 371 files · ~167,090 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2781 nodes · 5835 edges · 193 communities (138 shown, 55 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 590 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 161
- Community 162
- Community 171
- Community 172
- Community 176
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 190
- Community 191

## God Nodes (most connected - your core abstractions)
1. `cn()` - 123 edges
2. `NullGraphProvider` - 61 edges
3. `EmbeddingService` - 54 edges
4. `FileIndexer` - 54 edges
5. `Entity` - 50 edges
6. `Relationship` - 48 edges
7. `GraphProvider` - 47 edges
8. `ConversationRepository` - 44 edges
9. `GraphQueryService` - 42 edges
10. `DocumentRepository` - 41 edges

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

## Communities (193 total, 55 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (95): App, AppHandle, Arc, Child, Client, add_watched_folder(), AddFolderRequest, AppState (+87 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (54): FileProcessorPlugin, ABC, Path, Abstract base classes defining the extension points available to plugins. A…, Extract plain text from files of a custom type. Registered plugins are…, Return lowercase dot-prefixed extensions, e.g. ``frozenset({".abc"})``., Extract and return plain text from *file_path*. Must be synchronous. Raise…, Transform extracted text before it is chunked and embedded. Plugins in this… (+46 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (38): Entity, GraphContext, Context retrieved from the knowledge graph for a given query entity., Relationship, GraphProvider, ABC, Abstract interface for the knowledge graph provider. Business logic depends on…, Defines the contract for all graph storage backends. (+30 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (45): lifespan(), FastAPI application for the Enterprise AI Companion backend., Open all stores on startup; close them on shutdown., bulk_delete_documents(), BulkDeleteRequest, delete_document(), DocumentResponse, list_documents() (+37 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (39): BackupResultResponse, BackupSummaryResponse, create_backup(), CreateBackupRequest, delete_backup(), DeleteBackupResponse, _get_service(), list_backups() (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (45): ConnectedDocumentsResponse, _entity_to_response(), EntityResponse, EntitySearchResponse, find_path(), get_connected_documents(), get_entity_context(), get_graph_visualization() (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (39): MODES, ThemeToggle(), ThemeToggleProps, AIProviderSettings(), AIProviderSettingsProps, GeneralSettings(), GeneralSettingsProps, THEME_OPTIONS (+31 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (17): ConversationMemory, ConversationSummary, EmbedResponse, GraphContextResponse, GraphEntityItem, GraphHealthResponse, GraphRelationshipItem, HealthResponse (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (23): _coerce_entity_type(), EntityExtractor, _parse_json(), Any, Attempt to parse raw LLM output as JSON, stripping markdown fences., Extracts named entities from a text chunk via a structured LLM call. Usage:…, Return extracted entities from text. Returns [] on failure., ExtractedEntity (+15 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (45): Capability Model, AI Services Capability, Automation Capability, Conversation Capability, File Intelligence Capability, Knowledge Management Capability, Search & Retrieval Capability, Settings & Configuration Capability (+37 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (32): AssistantAvatar(), AssistantAvatarProps, SIZE_CLASSES, CitationChip(), CitationChipProps, ConversationViewProps, FilePathChip(), FilePathChipProps (+24 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (32): AssistantFooter(), AssistantFooterProps, AssistantHeader(), AssistantHeaderProps, resolveStatus(), AssistantStatus(), AssistantStatusProps, STATUS_CONFIG (+24 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (39): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+31 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (26): Logo(), LogoProps, PlaceholderPage(), PlaceholderPageProps, MainContent(), PAGE_MAP, PAGE_TRANSITION, PageModule (+18 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (22): _canonical(), Any, Connection, SQLite-backed knowledge graph provider. Implements the full GraphProvider…, Insert or update a directed relationship edge., Remove all entities (and cascade-delete their relationships) for a document., Return the named entity plus its neighbourhood up to *depth* hops. Depth is…, Case-insensitive substring search over entity names. (+14 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (28): ContextAssembler, ContextChunk, ContextPayload, Connection, QdrantClient, Context assembly service for the AI retrieval pipeline. Wraps the hybrid search…, Retrieve and assemble context chunks for the given query. Pipeline: 1. Hybrid…, Supplement vector-retrieved chunks with graph-neighbour chunks. For each token… (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.10
Nodes (18): _collect_files(), FileIndexer, _is_cloud_stub(), Path, Return True if the file is a OneDrive cloud-only placeholder. On non-Windows…, Recursively indexes text files in a workspace directory. For each file that is…, Return False if resolved is inside a blocked OS-critical directory., Index all supported files under workspace_path. Returns a summary. progress_cb… (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (7): DesktopPresenceService, ORB_OVERLAY_ID, OrbControllerState, OrbStateListener, Overlay, OverlayRegistry, makeService()

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (29): _get_db(), hybrid_search(), HybridSearchRequest, HybridSearchResponse, HybridSearchResultItem, keyword_search(), KeywordSearchRequest, KeywordSearchResponse (+21 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (35): autoprefixer, class-variance-authority, clsx, d3-force, dependencies, autoprefixer, class-variance-authority, clsx (+27 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (24): SuggestedQueries(), SuggestedQueriesProps, EmptySearchState(), EmptySearchStateProps, SearchFilters(), SearchFiltersProps, TOP_K_OPTIONS, SearchInput() (+16 more)

### Community 21 - "Community 21"
Cohesion: 0.17
Nodes (14): RelationshipType, _entity(), _make_provider(), Connection, Tests for SQLiteGraphProvider — all run in-memory, no external services., _rel(), _seed_doc(), TestDeleteByDocument (+6 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (7): NullGraphProvider, TestGraphQueryService, TestTraversalEngine, provider(), fixture, Tests for NullGraphProvider — verifies the no-op contract., TestNullGraphProvider

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (14): DocumentRepository, IndexedDocument, Connection, db(), _make_doc(), Connection, fixture, Unit tests for DocumentRepository using an in-memory SQLite database. (+6 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (20): PendingDelete, DocumentFilters(), DocumentFiltersProps, EXTENSION_OPTIONS, SORT_OPTIONS, DocumentRowProps, FolderRow(), FolderRowProps (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (26): ConversationMemoryResponse, ConversationResponse, ConversationSummaryResponse, get_conversation_memory(), get_db(), list_conversations(), load_conversation(), MessageResponse (+18 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (27): cancel_indexing(), clear_indexing_errors(), get_indexing_status(), IndexingErrorResponse, IndexingStatusResponse, list_indexing_errors(), Any, BaseModel (+19 more)

### Community 27 - "Community 27"
Cohesion: 0.10
Nodes (13): EmbeddingService, Generates dense text embeddings using bge-small-en-v1.5 locally via ONNX…, Return a single embedding vector for the given text. Args: text: The input…, Return embedding vectors for a list of texts. Args: texts: A non-empty list of…, Connection, QdrantClient, fixture, Unit tests for EmbeddingService. These tests load the real BGE-M3 model via… (+5 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (12): HybridSearchResult, Hybrid search orchestrator combining keyword and semantic search. Uses…, A single result from the hybrid search pipeline. The rrf_score is the combined…, Execute hybrid search and return merged results. Args: query: Preprocessed…, Keyword search provider backed by SQLite FTS5., Shared data models for the search capability., SearchResult, _make_client() (+4 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (29): Confidence Model, Context Engine, ContextSnapshot, Conversation Service, Desktop Companion, Desktop Presence Layer, Glass Prompt, Living Orb (+21 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (23): AttachmentButton(), AttachmentButtonProps, CONTEXT_ITEMS, ContextBar(), ContextBarProps, ContextItem, EdgeLabel(), EdgeLabelProps (+15 more)

### Community 31 - "Community 31"
Cohesion: 0.12
Nodes (13): canonical_name(), EnrichmentService, Knowledge graph enrichment service. Runs after entity and relationship…, Return a normalised lowercase key suitable for duplicate detection. Steps: 1.…, Post-extraction enrichment for the knowledge graph. Supports…, Run the full enrichment pipeline — merge duplicates across all entity types., Extracts named entities from text using a structured LLM call. Replaces the…, EntityType (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.07
Nodes (28): AbbreviationExtractor, FileIndexer, HybridSearchOrchestrator, KeywordSearchProvider (FTS5), KnowledgeGraphService, QdrantSearchProvider, QueryPreprocessor, Reciprocal Rank Fusion (RRF) (+20 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (27): BAAI/bge-small-en-v1.5 Embedding Model (384-dim), BM25 Keyword Search (SQLite FTS5), Character Bigram Cosine Reranker, chunk_repository.py, context_assembler.py, embedding_service.py, file_indexer.py, hybrid_orchestrator.py (+19 more)

### Community 34 - "Community 34"
Cohesion: 0.07
Nodes (26): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+18 more)

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (15): AbbreviationRepository, Connection, Async repository for the ``abbreviations`` table. Args: conn: An open…, Persist a batch of abbreviation matches for a single document. Uses ``INSERT OR…, Remove all abbreviation rows for the given document. Called before re-indexing…, Load all discovered abbreviations across every document. Returns a mapping…, AbbreviationExtractor, AbbreviationMatch (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (21): confidenceColor(), confidenceLabel(), EntityCard(), EntityCardProps, drawArrow(), drawFrame(), ENTITY_COLORS, entityColor() (+13 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (12): KeywordSearchProvider, Connection, Full-text keyword search over indexed document chunks using SQLite FTS5. The…, db(), asyncio, Connection, fixture, Tests for KeywordSearchProvider. (+4 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (18): STATUS_CLASSES, STATUS_LABELS, StatusIndicator(), StatusIndicatorProps, StatusVariant, DEFAULT_STATUS, fetchServiceStatus(), ServiceStatus (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.19
Nodes (17): applyFiltersAndSort(), DocumentBrowser(), FolderList(), formatTimestamp(), IndexingErrorsTab(), IndexingStatusPanel(), IndexingTaskCard(), IndexingTaskCardProps (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (8): ConversationRepository, Atomically increment turn_count and return the new value., Persist a compressed summary for the conversation., Async repository for conversation and message persistence., TestGetOrCreateConversation, TestListConversations, TestLoadConversation, TestSaveMessage

### Community 41 - "Community 41"
Cohesion: 0.16
Nodes (17): LivingOrb(), LivingOrbProps, OrbContainer(), OrbIcon(), OrbIconProps, ORB_BORDER_COLOR, ORB_FOCUS_RING, ORB_GRADIENT_FROM (+9 more)

### Community 42 - "Community 42"
Cohesion: 0.17
Nodes (6): QueryPreprocessor, QueryPreprocessorConfig, Transforms a raw user query into a structured ProcessedQuery. Designed to be…, Replace the dynamic expansion set with entries from discovered abbreviations.…, Feature flags for the preprocessing pipeline., TestQueryPreprocessor

### Community 43 - "Community 43"
Cohesion: 0.17
Nodes (14): OrbContainerProps, DragOrigin, useOrbDrag(), UseOrbDragOptions, UseOrbDragResult, useOrbPosition(), OrbLayer(), clamp() (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (7): Splits plain text into overlapping character-based chunks for embedding., Splits text into overlapping chunks, preferring sentence boundaries. Args:…, Return a list of (content, char_start, char_end) tuples. Chunks are at most…, Return the character position of the last sentence break in text, or 0., TextChunker, Unit tests for TextChunker., TestChunker

### Community 45 - "Community 45"
Cohesion: 0.19
Nodes (11): _client_with_watcher(), _make_watcher(), TestClient, WatchedFolder, Endpoint tests for the /watcher router. Injects a mock WatcherService into…, Build a minimal WatcherService mock for injection into app.state., Return a TestClient that has watcher injected after lifespan starts., TestAddFolder (+3 more)

### Community 46 - "Community 46"
Cohesion: 0.10
Nodes (21): @eslint/js, eslint-plugin-react, eslint-plugin-react-refresh, devDependencies, @eslint/js, eslint-plugin-react, eslint-plugin-react-refresh, jsdom (+13 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (18): add_watched_folder(), AddFolderRequest, get_watcher_status(), list_watched_folders(), BaseModel, delete, get, post (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.20
Nodes (5): ConversationServiceContext, LLMProvider, LLMRequestOptions, ConversationService, ConversationTurn

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (3): OrbController, makeControllableProvider(), renderIntegration()

### Community 50 - "Community 50"
Cohesion: 0.19
Nodes (6): OrbAnimationController, OrbAnimationDriver, OrbState, OrbStateListener, OrbStateMachine, TRANSITIONS

### Community 51 - "Community 51"
Cohesion: 0.11
Nodes (10): _build_graph_provider(), Return the appropriate graph provider based on EAC_GRAPH_PROVIDER. Default (no…, Neo4jProvider, Create or update a directed relationship between two entity nodes. Both nodes…, Return ``{"nodes": [...], "edges": [...]}`` for the graph UI. When…, Return entities whose names contain *query* (case-insensitive substring). Args:…, Return document IDs of all entities reachable (up to 2 hops) from entity_name., Remove all entity nodes (and their relationships) sourced from document_id. (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (10): ConversationSummary, Return all conversations, most recent first, with their message count., _make_message(), _mock_db_app(), Tests for the conversations FastAPI endpoints using an in-memory database., Return a TestClient with a mock db in app.state., TestListConversationsEndpoint, TestLoadConversationEndpoint (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.24
Nodes (6): Merge two ranked lists using Reciprocal Rank Fusion. Each chunk accumulates an…, _rrf_merge(), _make_result(), Verify the score for a chunk that appears at rank 1 in one list only., A chunk_id appearing in both lists should produce exactly one result., TestRrfMerge

### Community 54 - "Community 54"
Cohesion: 0.20
Nodes (9): App(), useDesktopPresence(), DesktopPresenceContext, DesktopPresenceProvider(), DesktopPresenceProviderProps, LayoutProvider(), LayoutProviderProps, OrbControllerProvider() (+1 more)

### Community 55 - "Community 55"
Cohesion: 0.29
Nodes (9): LocalFileConnector, OneDriveConnector, NullRetrievalBroker, DocumentFragment, RetrievalBroker, RetrievalQuery, RetrievalResult, ANY_QUERY (+1 more)

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (11): Conversation memory service — automatic summarisation of older turns. After…, ConversationMemoryState, Message, Conversation persistence repository. Provides async CRUD operations over the…, Persist a message, creating the parent conversation if needed., Return all messages for a conversation, oldest first., Return the turn_count and summary for a conversation. Creates the conversation…, Return up to `limit` messages, oldest first, for summarisation. (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.18
Nodes (9): Manages the watchdog Observer and the set of watched folders. Persists the…, Load persisted folders and start the watchdog Observer. Safe to call from…, Async start path — used when start() is called from inside the event loop., Register a new folder for watching. Triggers an immediate initial index., Persist a folder as watched and start the filesystem watch. Unlike add_folder,…, Return all registered watched folders., A folder registered for automatic background indexing., WatchedFolder (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.13
Nodes (10): APIMConfig, APIMChatCompletion, APIMChatMessage, APIMError, APIMRequestBody, APIMStreamDelta, RETRYABLE_STATUS_CODES, makeSSEStream() (+2 more)

### Community 60 - "Community 60"
Cohesion: 0.12
Nodes (17): Graphify Add URL Ingestion, Graphify Watch Folder Auto-Rebuild, MCP Server Graph Export, Wiki Export (Agent-Crawlable), Extraction Subagent Prompt, Cross-Repo Graph Merge, CLAUDE.md Graphify Integration, Post-Commit Auto-Rebuild Hook (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.19
Nodes (8): GraphStateRepository, Connection, SQLite-backed store for per-document graph build state., Insert or replace the graph state for document_id., Remove the graph state entry for document_id., Connection, Integration tests using an in-memory SQLite database., TestGraphStateRepository

### Community 62 - "Community 62"
Cohesion: 0.18
Nodes (7): KnowledgeGraphService, Orchestrates entity extraction and graph persistence for indexed documents.…, Extract entities/relationships from each chunk and persist to the graph. After…, Remove all graph nodes and relationships sourced from this document., fixture, service(), TestBuildFromChunks

### Community 63 - "Community 63"
Cohesion: 0.17
Nodes (7): _escape_fts5_query(), _normalise_bm25(), Escape a raw user query for safe use in an FTS5 MATCH expression. Wraps each…, Convert a raw SQLite BM25 score (negative, unbounded) to (0, 1]. SQLite's…, Return up to *top_k* chunks matching *query* via full-text search. Args: query:…, TestEscapeFts5Query, TestNormaliseBm25

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (13): health(), limit_request_body(), get, Reject requests that lack the per-session IPC shared secret. The token is…, Reject requests with a Content-Length header exceeding 10 MiB., Liveness probe used by the Tauri IPC health_check command., TokenVerificationMiddleware, QdrantProvider (+5 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (15): DashboardStats, _get_stats(), get_suggested_queries(), BaseModel, Connection, get, post, Request (+7 more)

### Community 66 - "Community 66"
Cohesion: 0.22
Nodes (15): _apply_migrations(), close_db(), _db_path(), _find_migrations_dir(), lifespan_db(), _migrations_dir(), open_db(), Connection (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.21
Nodes (12): _pid_file_path(), Path, QdrantClient, _qdrant_data_dir(), Local Qdrant vector store provider for the Enterprise AI Companion. Uses…, Open the local Qdrant store and ensure the collection exists with correct dims.…, Write the current process PID so the next startup can terminate this one., Kill the previously recorded PID if it is still running. (+4 more)

### Community 68 - "Community 68"
Cohesion: 0.18
Nodes (12): ACCENT_CLASSES, formatValue(), ICON_ACCENT_CLASSES, StatTile(), StatTileProps, CachedSuggestions, DashboardState, loadCachedSuggestions() (+4 more)

### Community 69 - "Community 69"
Cohesion: 0.13
Nodes (11): PERMISSION_LABELS, PluginSettings(), useEmbedding(), UseEmbeddingResult, IPCClient, PluginRecord, waitForSidecar(), mockInvoke (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.21
Nodes (12): cosine(), heuristicRerank(), ngramTf(), RankedCandidate, tokenise(), ContextEngineContext, ConversationIdContext, ConversationIdContextValue (+4 more)

### Community 71 - "Community 71"
Cohesion: 0.24
Nodes (14): ErrorOccurredEvent, HoverEnterEvent, HoverLeaveEvent, InputFinishedEvent, InputStartedEvent, NotificationReceivedEvent, OrbEvent, OrbEventType (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (7): db(), mock_indexer(), fixture, Unit tests for WatcherService and DebounceHandler., TestWatcherServiceFolders, TestWatcherServiceStart, watcher_service()

### Community 73 - "Community 73"
Cohesion: 0.19
Nodes (10): GlassPrompt(), GlassPromptProps, OVERLAY_VARIANTS, PANEL_VARIANTS, BackupSettings(), formatBytes(), formatDate(), Button (+2 more)

### Community 74 - "Community 74"
Cohesion: 0.28
Nodes (4): ContextEngine, ContextSnapshot, NullContextEngine, WorkspaceContextEngine

### Community 75 - "Community 75"
Cohesion: 0.23
Nodes (3): Notification, NotificationService, NullNotificationService

### Community 76 - "Community 76"
Cohesion: 0.20
Nodes (9): _has_fuzzy_candidates(), Enum, str, Query preprocessing pipeline for the search subsystem. Each stage is…, Return True if any token looks like it might be a typo. Heuristics: - Token…, Broad classification of the user's search intent., SearchIntent, Unit tests for the query preprocessing pipeline. (+1 more)

### Community 78 - "Community 78"
Cohesion: 0.26
Nodes (12): disable_plugin(), enable_plugin(), list_plugins(), PluginResponse, BaseModel, get, post, Request (+4 more)

### Community 79 - "Community 79"
Cohesion: 0.19
Nodes (9): AuditLogger, Any, Connection, Structured audit logging for security-relevant application events. Events are…, Return a copy of details with sensitive values replaced by '<redacted>'., Writes audit events to the audit_events table and the application log., Record a single audit event. Args: event_type: Dot-namespaced verb, e.g.…, Return the most recent audit events, newest first. (+1 more)

### Community 80 - "Community 80"
Cohesion: 0.23
Nodes (6): _make_client(), TestClient, Tests for the /graph API endpoints using NullGraphProvider injected into…, Return a TestClient with NullGraphProvider pre-loaded into app.state., TestGetGraphEntity, TestGraphHealth

### Community 81 - "Community 81"
Cohesion: 0.37
Nodes (3): asyncio, semantic_weight=0 should suppress semantic contribution., TestHybridSearchOrchestrator

### Community 82 - "Community 82"
Cohesion: 0.23
Nodes (12): AI Provider Abstraction Layer, BGE-M3 Embeddings, Engineering Specification (CLAUDE.md), Enterprise AI Companion, OpenAI GPT-5 Mini, PaddleOCR, Qdrant Vector Store, Tauri Desktop Framework (+4 more)

### Community 83 - "Community 83"
Cohesion: 0.23
Nodes (6): AbstractEventLoop, DebounceHandler, Connection, Watchdog event handler with per-path debouncing. Consecutive events for the…, FileSystemEvent, FileSystemEventHandler

### Community 84 - "Community 84"
Cohesion: 0.17
Nodes (11): description, identifier, permissions, $schema, windows, core:default, global-shortcut:allow-register, global-shortcut:allow-unregister (+3 more)

### Community 85 - "Community 85"
Cohesion: 0.18
Nodes (11): scripts, build, dev, format, lint, lint:fix, preview, tauri (+3 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (7): apimEndpoint, LLM_CONFIG, LLMConfig, LLMProviderKey, providerOverride, assertNever(), createLLMProvider()

### Community 87 - "Community 87"
Cohesion: 0.31
Nodes (4): GlassPromptContainer(), OrbControllerContext, GlassPromptStore, useGlassPromptStore

### Community 89 - "Community 89"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, types, include (+2 more)

### Community 90 - "Community 90"
Cohesion: 0.24
Nodes (8): find_free_port(), _load_env_file(), Uvicorn startup and shutdown for the Enterprise AI Companion backend., Load key=value pairs from backend/.env into os.environ (if the file exists).…, Bind to port 0 so the OS assigns a free port, then release and return it., Start uvicorn on the given port (or a free OS-assigned port)., run(), Entry point: python -m enterprise_ai_companion

### Community 91 - "Community 91"
Cohesion: 0.33
Nodes (3): _detect_intent(), Classify the query intent from the token set using signal words., TestDetectIntent

### Community 92 - "Community 92"
Cohesion: 0.24
Nodes (3): _patch_service(), Patch the EmbeddingService singleton used by the router., TestEmbeddingsEndpoint

### Community 93 - "Community 93"
Cohesion: 0.22
Nodes (9): Neo4j Graph Database, SQLite Database, Neo4j Cypher Export, Knowledge Graph Operations (Neo4j), Neo4j Docker Compose Service, GraphProvider Interface, Neo4jProvider, NullGraphProvider (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.39
Nodes (8): _api_key(), _base_url(), chat_complete(), _model_id(), Thin async wrapper around the Volvo GenAI Hub (OpenAI-compatible) API.…, Send a chat completion request and return the assistant message content.…, get_config(), Return the singleton AppConfig, creating it on first call. Raises…

### Community 95 - "Community 95"
Cohesion: 0.33
Nodes (3): _is_excluded(), Return True if any segment of path is in EXCLUDED_DIRS., TestIsExcluded

### Community 96 - "Community 96"
Cohesion: 0.36
Nodes (3): _expand(), Return additional terms for tokens that match the expansion dictionaries.…, TestExpand

### Community 97 - "Community 97"
Cohesion: 0.36
Nodes (3): _normalise(), Lowercase, unicode-normalise (NFC), and collapse internal whitespace., TestNormalise

### Community 98 - "Community 98"
Cohesion: 0.36
Nodes (3): _make_handler(), Create a DebounceHandler with a fresh non-running loop (timers only)., TestDebounceHandler

### Community 99 - "Community 99"
Cohesion: 0.22
Nodes (8): name, pnpm, onlyBuiltDependencies, private, type, version, esbuild, @tauri-apps/cli

### Community 100 - "Community 100"
Cohesion: 0.33
Nodes (5): MOCK_RESPONSE_TABLE, MockProvider, MockResponseEntry, resolveResponse(), sleep()

### Community 101 - "Community 101"
Cohesion: 0.47
Nodes (3): NullProjectKnowledgeRepository, Project, ProjectKnowledgeRepository

### Community 102 - "Community 102"
Cohesion: 0.29
Nodes (7): create_embedding(), EmbedRequest, EmbedResponse, BaseModel, field_validator, post, Generate a BGE-M3 embedding vector for the supplied text. Returns a…

### Community 103 - "Community 103"
Cohesion: 0.29
Nodes (4): IndexingError, IndexingErrorRepository, Connection, Persists per-file indexing failures to SQLite.

### Community 104 - "Community 104"
Cohesion: 0.39
Nodes (3): Split on whitespace and punctuation, keeping hyphenated compounds whole. Tokens…, _tokenise(), TestTokenise

### Community 105 - "Community 105"
Cohesion: 0.39
Nodes (3): Remove tokens that are in the stop-word list., _remove_stop_words(), TestRemoveStopWords

### Community 106 - "Community 106"
Cohesion: 0.29
Nodes (3): Cancel pending debounce timers — called when a watch is removed., Stop the Observer and cancel all pending debounce timers., Unregister a folder and stop watching it.

### Community 107 - "Community 107"
Cohesion: 0.43
Nodes (3): _looks_like_typo(), Return True when the token exhibits common typo patterns. Checks: 1. Repeated…, TestLooksLikeTypo

### Community 108 - "Community 108"
Cohesion: 0.29
Nodes (6): AppConfig, Centralised application configuration for the Enterprise AI Companion. All…, Application configuration loaded from environment variables and .env file., Reset the singleton — intended for use in tests only., reset_config(), BaseSettings

### Community 110 - "Community 110"
Cohesion: 0.33
Nodes (6): db(), Connection, fixture, Unit tests for ConversationRepository using an in-memory SQLite database., In-memory SQLite database with schema applied, closed after each test., repo()

### Community 111 - "Community 111"
Cohesion: 0.48
Nodes (6): fileName(), formatDate(), OpenButton(), RecentFilesList(), RecentFilesListProps, RecentFile

### Community 112 - "Community 112"
Cohesion: 0.48
Nodes (6): DocumentRow(), EXT_ICONS, formatDate(), formatSize(), getExtension(), getFileName()

### Community 113 - "Community 113"
Cohesion: 0.43
Nodes (3): BackupResult, BackupSummary, SettingsService

### Community 114 - "Community 114"
Cohesion: 0.48
Nodes (6): build_pdf(), build_styles(), code_block(), _content_page(), _cover_page_bg(), Generate a well-formatted PDF describing the Enterprise AI Companion search…

### Community 115 - "Community 115"
Cohesion: 0.33
Nodes (6): Capability-Based Organization, Clean Architecture Principle, Capability Layer, Domain Layer, External Systems, Infrastructure Layer

### Community 116 - "Community 116"
Cohesion: 0.33
Nodes (4): _auth(), Connect to Neo4j and create uniqueness constraints + indexes., Create uniqueness constraint on Entity.id (idempotent in Neo4j 5)., _uri()

### Community 117 - "Community 117"
Cohesion: 0.33
Nodes (6): BGE-M3 Embedding Service, ConversationRepository, IPCClient, Python Sidecar (FastAPI), ConversationMemoryService, Home Page Dashboard

### Community 118 - "Community 118"
Cohesion: 0.40
Nodes (5): Architecture Decision Records (ADRs), Layered Architecture, Application Layer, Presentation Layer, Architecture Documentation Suite

### Community 119 - "Community 119"
Cohesion: 0.40
Nodes (5): File Indexing Capability, FileConnector Interface, FileIndexer, LocalFileConnector, OneDriveConnector

### Community 121 - "Community 121"
Cohesion: 0.50
Nodes (5): lint-staged, src/**/*.{json,css,md}, src/**/*.{ts,tsx}, eslint --fix, prettier --write

### Community 122 - "Community 122"
Cohesion: 0.40
Nodes (5): Tauri Framework Logo, App Icon 128x128, App Icon 32x32, Enterprise AI Companion App Icon (main), App Store Logo

### Community 124 - "Community 124"
Cohesion: 0.50
Nodes (3): ProcessedQuery, Run the full preprocessing pipeline on raw_query. Args: raw_query: Unmodified…, Result of running a raw query through the preprocessing pipeline. Attributes:…

### Community 125 - "Community 125"
Cohesion: 0.67
Nodes (3): BFS Graph Traversal Query, Save Result Feedback Loop, Query Vocabulary Expansion

### Community 128 - "Community 128"
Cohesion: 0.67
Nodes (3): BackupService, Settings Page, Settings Service (Frontend)

## Knowledge Gaps
- **366 isolated node(s):** `enterprise-ai-companion`, `$schema`, `style`, `rsc`, `tsx` (+361 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FileIndexer` connect `Community 16` to `Community 64`, `Community 1`, `Community 2`, `Community 3`, `Community 35`, `Community 103`, `Community 44`, `Community 83`, `Community 22`, `Community 23`, `Community 57`, `Community 26`, `Community 27`, `Community 61`, `Community 62`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `NullGraphProvider` connect `Community 22` to `Community 64`, `Community 2`, `Community 3`, `Community 35`, `Community 8`, `Community 15`, `Community 16`, `Community 80`, `Community 51`, `Community 26`, `Community 61`, `Community 62`, `Community 31`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `NullGraphProvider` (e.g. with `TokenVerificationMiddleware` and `BulkDeleteRequest`) actually correct?**
  _`NullGraphProvider` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `EmbeddingService` (e.g. with `TokenVerificationMiddleware` and `EmbedRequest`) actually correct?**
  _`EmbeddingService` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `FileIndexer` (e.g. with `TokenVerificationMiddleware` and `IndexingErrorResponse`) actually correct?**
  _`FileIndexer` has 24 INFERRED edges - model-reasoned connections that need verification._
- **What connects `enterprise-ai-companion`, `$schema`, `style` to the rest of the system?**
  _366 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09407216494845361 - nodes in this community are weakly interconnected._