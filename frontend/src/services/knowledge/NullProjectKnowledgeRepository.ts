import type { Project, ProjectKnowledgeRepository } from "./ProjectKnowledgeRepository";

/**
 * Phase 00 implementation of ProjectKnowledgeRepository.
 *
 * Always returns null — no projects are registered in Phase 00. The
 * ProjectKnowledgeRepository persistence layer is introduced in Phase 01
 * when the indexing pipeline and project management UI are implemented.
 */
export class NullProjectKnowledgeRepository implements ProjectKnowledgeRepository {
  async findByFolderPath(_folderPath: string): Promise<Project | null> {
    return null;
  }
}
