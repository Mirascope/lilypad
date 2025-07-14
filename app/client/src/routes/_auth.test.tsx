import { AuthLayout } from "@/src/routes/_auth";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("AuthLayout", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render auth layout", async () => {
    await renderRoute({
      path: "/_auth",
      component: AuthLayout,
      authContext: mockAuthenticatedContext,
      initialPath: "/_auth",
    });

    // The auth layout renders the sidebar and outlet, so check for the sidebar
    await waitFor(() => {
      expect(screen.getByText("Lilypad")).toBeTruthy();
    });
  });
});