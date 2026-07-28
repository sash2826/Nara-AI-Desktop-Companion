/**
 * A user-defined project — the fundamental unit of knowledge organisation.
 *
 * `id` is the stable identifier used by all services. `folderPath` is how
 * the Context Engine resolves the active project from a file system signal.
 */
export interface Project {
  /** Stable UUID assigned at creation. Never changes. */
  id: string;
  /** Human-readable name chosen by the user. */
  name: string;
  /** Absolute path of the project's primary folder on the local file system. */
  folderPath: string;
  /** ISO 8601 timestamp of when the project was created. */
  createdAt: string;
}

/**
 * Read interface for the Project Knowledge Layer.
 *
 * The Context Engine uses this repository to resolve a file system path to a
 * Project entity when building a ContextSnapshot. The Conversation Service
 * uses the resolved Project to scope retrieval queries.
 *
 * This is a read-only interface from the companion's perspective during a
 * conversation. Write paths (indexing pipeline, conversation processing) are
 * defined separately and introduced in a later phase.
 */
export interface ProjectKnowledgeRepository {
  /**
   * Find the project whose `folderPath` matches the given path.
   *
   * Returns `null` if no project is registered for that path.
   */
  findByFolderPath(folderPath: string): Promise<Project | null>;
}
