## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Roadmap and Architecture — Always Verify via Graph

NEVER recite the project phase status, roadmap, or architecture from memory or from stale documentation files. Implementation docs (docs/implementation/README.md, phase docs) lag behind the actual codebase and WILL be wrong.

Before making any claim about:
- Which phases are complete, in progress, or planned
- What has or has not been implemented
- The current architecture of any capability
- Dependencies between phases

**Always run `graphify query "<question>"` first**, then cross-check against the actual source files if the graph result is ambiguous. If the docs contradict what the code shows, trust the code and flag the doc as stale.

This rule exists because reciting stale phase status caused incorrect roadmap advice. The graph reflects the actual codebase; docs do not.
