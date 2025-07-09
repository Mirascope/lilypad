import { ComparePlaygroundsRoute } from "@/src/routes/_auth/projects/$projectUuid/playground/$functionName/compare.$firstFunctionUuid.$secondFunctionUuid";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, mock } from "bun:test";

describe("ComparePlaygroundsRoute", () => {
  beforeAll(() => {
    setupTestEnvironment();

    // Mock the functions data to include both first and second function UUIDs with versioned functions
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
            is_versioned: true,
          },
          {
            uuid: "test-second-function-uuid", 
            name: "test_function",
            version_num: 2,
            project_uuid: "test-project-uuid",
            created_at: new Date().toISOString(),
            is_versioned: true,
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

    // Mock EE playground functions
    void mock.module("@/src/ee/utils/functions", () => ({
      useRunPlaygroundMutation: mock(() => ({
        mutateAsync: mock(() => Promise.resolve({
          success: true,
          data: { trace_context: { span_uuid: "test-span-uuid" } }
        })),
        isPending: false,
      })),
    }));

    // Mock feature access to disable playground to avoid complex EE component rendering
    void mock.module("@/src/hooks/use-featureaccess", () => ({
      useFeatureAccess: mock(() => ({
        playground: false,
        functions: true,
        traces: true,
        annotations: false,
      })),
    }));
  });

  it("should render compare playgrounds route", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid",
      component: ComparePlaygroundsRoute,
      authContext: mockAuthenticatedContext,
      params: {
        projectUuid: "test-project-uuid",
        functionName: "test_function",
        firstFunctionUuid: "test-first-function-uuid",
        secondFunctionUuid: "test-second-function-uuid",
      },
    });

    expect(screen.getByText("Compare Functions")).toBeTruthy();
    expect(screen.getByText("Comparison requires versioned functions and playground access.")).toBeTruthy();
  });
});