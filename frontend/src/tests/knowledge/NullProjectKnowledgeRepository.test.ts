import { describe, it, expect } from "vitest";
import { NullProjectKnowledgeRepository } from "@/services/knowledge/NullProjectKnowledgeRepository";

describe("NullProjectKnowledgeRepository", () => {
  const repo = new NullProjectKnowledgeRepository();

  it("findByFolderPath returns null for any path", async () => {
    const result = await repo.findByFolderPath("/projects/q4-planning");

    expect(result).toBeNull();
  });

  it("findByFolderPath returns null for an empty string", async () => {
    const result = await repo.findByFolderPath("");

    expect(result).toBeNull();
  });

  it("findByFolderPath resolves (is not rejected)", async () => {
    await expect(repo.findByFolderPath("/any/path")).resolves.toBeNull();
  });
});
