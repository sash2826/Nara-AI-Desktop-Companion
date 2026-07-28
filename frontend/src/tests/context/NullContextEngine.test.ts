import { describe, it, expect } from "vitest";
import { NullContextEngine } from "@/services/context/NullContextEngine";

describe("NullContextEngine", () => {
  const engine = new NullContextEngine();

  it("getSnapshot resolves to an empty snapshot", async () => {
    const snapshot = await engine.getSnapshot();

    expect(snapshot.activeProjectFolder).toBeNull();
    expect(snapshot.recentDocuments).toEqual([]);
    expect(snapshot.explicitContext).toBeNull();
  });

  it("getSnapshot resolves (is not rejected)", async () => {
    await expect(engine.getSnapshot()).resolves.toBeDefined();
  });

  it("getSnapshot returns a new object on each call", async () => {
    const a = await engine.getSnapshot();
    const b = await engine.getSnapshot();

    expect(a).not.toBe(b);
  });
});
