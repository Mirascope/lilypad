import { Projects } from "@/src/routes/_auth/projects/index";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("Projects", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render projects page", async () => {
    await renderRoute({
      path: "/_auth/projects/",
      component: Projects,
      authContext: mockAuthenticatedContext,
      validateSearch: (search) => ({
        redirect: (search.redirect as string) || undefined,
        joined: (search.joined as boolean) || undefined,
      }),
    });

    await waitFor(() => {
      expect(screen.getByText("Projects")).toBeTruthy();
      expect(screen.getByText("Select a project to view functions.")).toBeTruthy();
    });
  });
});