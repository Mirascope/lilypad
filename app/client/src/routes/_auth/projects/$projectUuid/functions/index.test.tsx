import { FunctionsList } from "@/src/routes/_auth/projects/$projectUuid/functions/index";
import { setupTestEnvironment } from "@/src/test-setup";
import { beforeAll, describe, expect, it } from "bun:test";

describe("FunctionsList", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render functions list", async () => {
    expect(() => FunctionsList()).not.toThrow();
  });
});
