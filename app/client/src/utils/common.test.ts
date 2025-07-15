import { describe, expect, it } from "bun:test";

describe("Sample test suite", () => {
  it("should verify bun test is working", () => {
    expect(2 + 2).toBe(4);
  });

  it("should handle async operations", async () => {
    const result = await Promise.resolve("test");
    expect(result).toBe("test");
  });
});
