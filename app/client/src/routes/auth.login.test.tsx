import { LoginComponent } from "@/src/routes/auth.login";
import { renderRoute, mockAuthContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("LoginComponent", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render login page", async () => {
    await renderRoute({
      path: "/auth/login",
      component: LoginComponent,
      authContext: mockAuthContext,
      validateSearch: (search) => ({
        redirect: (search.redirect as string) || undefined,
      }),
    });

    expect(screen.getByText("Welcome to Lilypad")).toBeTruthy();
    expect(screen.getByText("Sign in to continue")).toBeTruthy();
  });

  it("should render with redirect parameter", async () => {
    await renderRoute({
      path: "/auth/login",
      component: LoginComponent,
      authContext: mockAuthContext,
      validateSearch: (search) => ({
        redirect: (search.redirect as string) || undefined,
      }),
      search: { redirect: "/projects" },
    });

    expect(screen.getByText("Welcome to Lilypad")).toBeTruthy();
    expect(screen.getByText("Sign in to continue")).toBeTruthy();
  });
});