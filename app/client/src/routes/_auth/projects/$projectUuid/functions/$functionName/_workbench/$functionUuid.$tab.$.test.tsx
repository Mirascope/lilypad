import { FunctionWorkbench } from "@/src/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, mock } from "bun:test";

describe("FunctionWorkbench", () => {
  beforeAll(() => {
    setupTestEnvironment();

    // Mock the functions data to include the function UUID
    void mock.module("@/src/utils/functions", () => ({
      functionsByNameQueryOptions: mock(() => ({
        queryKey: ["functionsByName", "test_function", "test-project-uuid"],
        queryFn: () => Promise.resolve([
          {
            uuid: "test-function-uuid",
            name: "test_function",
            version_num: 1,
            project_uuid: "test-project-uuid",
            created_at: new Date().toISOString(),
            code: "def test_function():\n    return 'Hello, World!'",
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

  it("should render function workbench", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab/$",
      component: FunctionWorkbench,
      authContext: mockAuthenticatedContext,
      params: {
        projectUuid: "test-project-uuid",
        functionName: "test_function",
        functionUuid: "test-function-uuid",
        tab: "overview",
      },
    });

    expect(screen.getByRole("heading", { name: "test_function" })).toBeTruthy();
    expect(screen.getByText("Back to Functions")).toBeTruthy();
    expect(screen.getByText("Compare")).toBeTruthy();
  });
});