import { Settings } from "@/src/routes/_auth/settings.$";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it, mock } from "bun:test";

describe("Settings", () => {
  beforeAll(() => {
    setupTestEnvironment();

    // Mock the tanstack router navigate to prevent navigation during test
    mock.module("@tanstack/react-router", () => {
      const original = require("@tanstack/react-router");
      return {
        ...original,
        useNavigate: () => mock(() => Promise.resolve()),
      };
    });
  });

  it("should render settings page", async () => {
    await renderRoute({
      path: "/_auth/settings/$",
      component: Settings,
      authContext: mockAuthenticatedContext,
      initialPath: "/_auth/settings/overview",
      params: { _splat: "overview" },
    });

    await waitFor(() => {
      expect(screen.getByText("Settings")).toBeTruthy();
    });
  });
});
