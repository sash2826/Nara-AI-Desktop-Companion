import { describe, it, expect } from "vitest";
import { NullRetrievalBroker } from "@/services/retrieval/NullRetrievalBroker";
import type { RetrievalQuery } from "@/services/retrieval/RetrievalBroker";

const ANY_QUERY: RetrievalQuery = {
  text: "quarterly report",
  projectFolder: "/projects/q4",
  maxResults: 5,
};

const NULL_FOLDER_QUERY: RetrievalQuery = {
  text: "quarterly report",
  projectFolder: null,
  maxResults: 10,
};

describe("NullRetrievalBroker", () => {
  const broker = new NullRetrievalBroker();

  it("retrieve resolves to an empty fragment list", async () => {
    const result = await broker.retrieve(ANY_QUERY);

    expect(result.fragments).toEqual([]);
  });

  it("retrieve with null projectFolder resolves to an empty fragment list", async () => {
    const result = await broker.retrieve(NULL_FOLDER_QUERY);

    expect(result.fragments).toEqual([]);
  });

  it("retrieve resolves (is not rejected)", async () => {
    await expect(broker.retrieve(ANY_QUERY)).resolves.toBeDefined();
  });
});
