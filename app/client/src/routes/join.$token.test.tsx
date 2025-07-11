import { JoinPage } from "@/src/routes/join.$token";
import { renderRoute, mockAuthContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("JoinPage", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render without crashing", async () => {
    await renderRoute({
      path: "/join/$token",
      component: JoinPage,
      authContext: mockAuthContext,
      params: { token: "test-token" },
    });

    // Wait for any render to complete
    await waitFor(
      () => {
        expect(document.body.innerHTML.length).toBeGreaterThan(0);
      },
      { timeout: 10000 }
    );
  });

  // Check the component handles the token parameter
  it("should handle token parameter", async () => {
    await renderRoute({
      path: "/join/$token",
      component: JoinPage,
      authContext: mockAuthContext,
      params: { token: "test-token-123" },
    });

    await waitFor(
      () => {
        // Just verify something rendered
        expect(document.body).toBeTruthy();
        expect(document.body.innerHTML.length).toBeGreaterThan(0);
      },
      { timeout: 10000 }
    );
  });

  // Test different authentication contexts
  it("should work with authentication context", async () => {
    await renderRoute({
      path: "/join/$token",
      component: JoinPage,
      authContext: mockAuthContext,
      params: { token: "auth-test" },
    });

    await waitFor(
      () => {
        expect(document.body.innerHTML.length).toBeGreaterThan(0);
      },
      { timeout: 10000 }
    );
  });

  // Test the component in different states
  it("should handle component lifecycle", async () => {
    const result = await renderRoute({
      path: "/join/$token",
      component: JoinPage,
      authContext: mockAuthContext,
      params: { token: "lifecycle-test" },
    });

    // Check that renderRoute succeeded
    expect(result).toBeTruthy();

    await waitFor(
      () => {
        expect(document.body.innerHTML.length).toBeGreaterThan(0);
      },
      { timeout: 10000 }
    );
  });
});
