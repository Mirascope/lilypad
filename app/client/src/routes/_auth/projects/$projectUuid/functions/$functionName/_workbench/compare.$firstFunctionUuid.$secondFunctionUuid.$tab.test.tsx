import { CompareWorkbench } from "@/src/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare.$firstFunctionUuid.$secondFunctionUuid.$tab";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it, mock } from "bun:test";

describe("CompareWorkbench", () => {
  beforeAll(() => {
    setupTestEnvironment();

    // Mock the functions data to include both first and second function UUIDs
    void mock.module("@/src/utils/functions", () => ({
      functionsByNameQueryOptions: mock(() => ({
        queryKey: ["functionsByName", "test_function", "test-project-uuid"],
        queryFn: () => Promise.resolve([
          {
            uuid: "test-first-function-uuid",
            name: "test_function",
            version_num: 1,
            project_uuid: "test-project-uuid",
            created_at: new Date().toISOString(),
          },
          {
            uuid: "test-second-function-uuid", 
            name: "test_function",
            version_num: 2,
            project_uuid: "test-project-uuid",
            created_at: new Date().toISOString(),
          }
        ]),
      })),
      useArchiveFunctionByNameMutation: mock(() => ({
        mutateAsync: mock(() => Promise.resolve({})),
        isPending: false,
      })),
      useArchiveFunctionMutation: mock(() => ({
        mutateAsync: mock(() => Promise.resolve({})),
        isPending: false,
      })),
      usePatchFunctionMutation: mock(() => ({
        mutateAsync: mock(() => Promise.resolve({})),
        isPending: false,
      })),
      useCreateVersionedFunctionMutation: mock(() => ({
        mutateAsync: mock(() => Promise.resolve({})),
        isPending: false,
      })),
      functionKeys: {
        list: mock(() => ["functions", "list"]),
        byName: mock(() => ["functions", "byName"]),
      },
      uniqueLatestVersionFunctionNamesQueryOptions: mock(() => ({
        queryKey: ["uniqueLatestVersionFunctionNames"],
        queryFn: () => Promise.resolve([]),
      })),
      fetchFunctionsByName: mock(() => Promise.resolve([])),
      functionsQueryOptions: mock(() => ({
        queryKey: ["functions"],
        queryFn: () => Promise.resolve([]),
      })),
    }));

    // Mock the tanstack router navigate to prevent navigation during test
    void mock.module("@tanstack/react-router", () => {
      const original = import("@tanstack/react-router");
      return {
        ...original,
        useNavigate: () => mock(() => Promise.resolve()),
      };
    });
  });

  it("should render compare workbench", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab",
      component: CompareWorkbench,
      authContext: mockAuthenticatedContext,
      params: {
        projectUuid: "test-project-uuid",
        functionName: "test_function",
        firstFunctionUuid: "test-first-function-uuid",
        secondFunctionUuid: "test-second-function-uuid",
        tab: "overview",
      },
    });

    await waitFor(() => {
      expect(screen.getByText("test_function")).toBeTruthy();
      expect(screen.getByText("Back to Functions")).toBeTruthy();
      expect(screen.getByText("Compare")).toBeTruthy();
    });
  });
});