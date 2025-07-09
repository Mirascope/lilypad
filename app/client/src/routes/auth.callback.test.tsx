import { CallbackPage } from "@/src/routes/auth.callback";
import { setupTestEnvironment } from "@/src/test-setup";
import { mockAuthContext, renderRoute } from "@/src/test-utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it, mock } from "bun:test";

describe("CallbackPage", () => {
  beforeAll(() => {
    setupTestEnvironment();

    // Mock the tanstack router navigate to prevent navigation during test
    void mock.module("@tanstack/react-router", () => {
      const original = import("@tanstack/react-router");
      return {
        ...original,
        useNavigate: () => mock(() => Promise.resolve()),
      };
    });
  });

  it("should render callback page", async () => {
    await renderRoute({
      path: "/auth/callback",
      component: CallbackPage,
      authContext: mockAuthContext,
      validateSearch: (search) => {
        // Make sure we always return a valid code
        const code = search.code ?? "test-code";
        if (typeof code !== "string" || !code) {
          throw new Error("Invalid code");
        }
        return {
          code,
          state: search.state as string,
        };
      },
      search: { code: "test-code" },
    });

    await waitFor(() => {
      expect(screen.getByText("Processing login...")).toBeTruthy();
      expect(screen.getByText("Authenticating with github...")).toBeTruthy();
    });
  });
});
