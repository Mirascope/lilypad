import { JoinPage } from "@/src/routes/join.$token";
import { renderRoute, mockAuthContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("JoinPage", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render join page loading state", async () => {
    await renderRoute({
      path: "/join/$token",
      component: JoinPage,
      authContext: mockAuthContext,
      params: { token: "test-token" },
    });

    expect(await screen.findByText("Processing your invite...")).toBeTruthy();
  });
});