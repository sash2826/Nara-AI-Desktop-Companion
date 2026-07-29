import { describe, it, expect, beforeEach } from "vitest";
import { WorkspaceContextEngine } from "@/services/context/WorkspaceContextEngine";

describe("WorkspaceContextEngine", () => {
  let engine: WorkspaceContextEngine;

  beforeEach(() => {
    engine = new WorkspaceContextEngine();
  });

  // ─── Initial state ──────────────────────────────────────────────────────────

  it("getSnapshot returns null activeProjectFolder when no file has been recorded", async () => {
    const snapshot = await engine.getSnapshot();
    expect(snapshot.activeProjectFolder).toBeNull();
  });

  it("getSnapshot returns empty recentDocuments when no file has been recorded", async () => {
    const snapshot = await engine.getSnapshot();
    expect(snapshot.recentDocuments).toEqual([]);
  });

  it("getSnapshot returns null explicitContext (Phase 01)", async () => {
    const snapshot = await engine.getSnapshot();
    expect(snapshot.explicitContext).toBeNull();
  });

  // ─── recordActiveFile ───────────────────────────────────────────────────────

  it("derives activeProjectFolder from a Unix-style path", async () => {
    engine.recordActiveFile("/home/user/projects/my-app/src/main.ts");
    const snapshot = await engine.getSnapshot();
    expect(snapshot.activeProjectFolder).toBe("/home/user/projects/my-app/src");
  });

  it("derives activeProjectFolder from a Windows-style path", async () => {
    engine.recordActiveFile("C:\\Users\\user\\projects\\app\\src\\index.ts");
    const snapshot = await engine.getSnapshot();
    expect(snapshot.activeProjectFolder).toBe("C:/Users/user/projects/app/src");
  });

  it("derives activeProjectFolder for a file at root level", async () => {
    engine.recordActiveFile("/file.txt");
    const snapshot = await engine.getSnapshot();
    // No parent directory — returns the path itself
    expect(snapshot.activeProjectFolder).toBe("/file.txt");
  });

  it("adds the recorded file to recentDocuments", async () => {
    engine.recordActiveFile("/projects/app/src/main.ts");
    const snapshot = await engine.getSnapshot();
    expect(snapshot.recentDocuments).toContain("/projects/app/src/main.ts");
  });

  // ─── FIFO cap at 5 ─────────────────────────────────────────────────────────

  it("recentDocuments accumulates up to 5 paths", async () => {
    for (let i = 1; i <= 5; i++) {
      engine.recordActiveFile(`/projects/file${i}.ts`);
    }
    const snapshot = await engine.getSnapshot();
    expect(snapshot.recentDocuments).toHaveLength(5);
  });

  it("recentDocuments evicts the oldest entry when a 6th file is recorded", async () => {
    for (let i = 1; i <= 6; i++) {
      engine.recordActiveFile(`/projects/file${i}.ts`);
    }
    const snapshot = await engine.getSnapshot();
    expect(snapshot.recentDocuments).toHaveLength(5);
    expect(snapshot.recentDocuments).not.toContain("/projects/file1.ts");
    expect(snapshot.recentDocuments).toContain("/projects/file6.ts");
  });

  it("most recent file appears first in recentDocuments", async () => {
    engine.recordActiveFile("/projects/old.ts");
    engine.recordActiveFile("/projects/new.ts");
    const snapshot = await engine.getSnapshot();
    expect(snapshot.recentDocuments[0]).toBe("/projects/new.ts");
  });

  // ─── Deduplication ──────────────────────────────────────────────────────────

  it("recording the same file twice does not create duplicates", async () => {
    engine.recordActiveFile("/projects/main.ts");
    engine.recordActiveFile("/projects/other.ts");
    engine.recordActiveFile("/projects/main.ts");
    const snapshot = await engine.getSnapshot();
    const count = snapshot.recentDocuments.filter((p) => p === "/projects/main.ts").length;
    expect(count).toBe(1);
  });

  it("re-recording an existing file moves it to the front", async () => {
    engine.recordActiveFile("/projects/a.ts");
    engine.recordActiveFile("/projects/b.ts");
    engine.recordActiveFile("/projects/a.ts");
    const snapshot = await engine.getSnapshot();
    expect(snapshot.recentDocuments[0]).toBe("/projects/a.ts");
  });

  // ─── Snapshot isolation ─────────────────────────────────────────────────────

  it("getSnapshot returns a new recentDocuments array on each call", async () => {
    engine.recordActiveFile("/projects/main.ts");
    const a = await engine.getSnapshot();
    const b = await engine.getSnapshot();
    expect(a.recentDocuments).not.toBe(b.recentDocuments);
  });

  it("mutating a returned snapshot does not affect the engine's internal state", async () => {
    engine.recordActiveFile("/projects/main.ts");
    const snapshot = await engine.getSnapshot();
    snapshot.recentDocuments.push("/injected/path.ts");
    const next = await engine.getSnapshot();
    expect(next.recentDocuments).not.toContain("/injected/path.ts");
  });
});
