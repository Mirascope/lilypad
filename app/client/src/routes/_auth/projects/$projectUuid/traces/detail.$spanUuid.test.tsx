import { SpanDetailPage } from "@/src/routes/_auth/projects/$projectUuid/traces/detail.$spanUuid";
import { setupTestEnvironment } from "@/src/test-setup";
import { mockAuthenticatedContext, renderRoute } from "@/src/test-utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("SpanDetailPage", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render span detail page", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/traces/detail/$spanUuid",
      component: SpanDetailPage,
      authContext: mockAuthenticatedContext,
      params: { projectUuid: "test-project-uuid", spanUuid: "test-span-uuid" },
      initialPath: "/_auth/projects/test-project-uuid/traces/detail/test-span-uuid",
    });

    await waitFor(() => {
      expect(screen.getByText("Trace Hierarchy")).toBeTruthy();
    });
  });
});
