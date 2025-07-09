import { TraceContainer } from "@/src/routes/_auth/projects/$projectUuid/traces.$";
import { setupTestEnvironment } from "@/src/test-setup";
import { mockAuthenticatedContext, renderRoute } from "@/src/test-utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("Trace", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render traces page", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/traces/$",
      component: TraceContainer,
      authContext: mockAuthenticatedContext,
      params: { projectUuid: "test-project-uuid", _splat: "spans" },
      initialPath: "/_auth/projects/test-project-uuid/traces/spans",
    });

    await waitFor(() => {
      expect(screen.getByText("Test Project") || screen.getByTestId("lilypad-loading")).toBeTruthy();
    });
  });
});
