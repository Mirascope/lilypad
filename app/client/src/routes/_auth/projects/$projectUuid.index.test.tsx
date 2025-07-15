import { ProjectDashboard } from "@/src/routes/_auth/projects/$projectUuid.index";
import { setupTestEnvironment } from "@/src/test-setup";
import { mockAuthenticatedContext, renderRoute } from "@/src/test-utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("ProjectDashboard", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render project dashboard", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/",
      component: ProjectDashboard,
      authContext: mockAuthenticatedContext,
      params: { projectUuid: "test-project-uuid" },
      initialPath: "/_auth/projects/test-project-uuid/",
    });

    await waitFor(() => {
      expect(screen.getByText("Total Cost")).toBeTruthy();
      expect(screen.getByText("Total Tokens")).toBeTruthy();
      expect(screen.getByText("Total API Calls")).toBeTruthy();
    });
  });
});
