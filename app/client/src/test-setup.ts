import { mock } from "bun:test";

// Common API mocks that can be reused across tests
export const setupCommonMocks = () => {
  // Mock the API module completely to prevent network requests
  void mock.module("@/src/api", () => ({
    default: {
      get: mock(() => Promise.resolve({ data: { privacyVersion: "1.0.0", termsVersion: "1.0.0" } })),
      post: mock(() => Promise.resolve({ data: { url: "https://github.com/login" } })),
    },
    baseURL: "http://localhost:8000/v0",
  }));

  // Mock auth utils to prevent network requests
  void mock.module("@/src/utils/auth", () => ({
    fetchVersions: mock(() => Promise.resolve({ privacyVersion: "1.0.0", termsVersion: "1.0.0" })),
    getGithubSigninUrl: mock(() => Promise.resolve("https://github.com/login")),
    getGoogleSigninUrl: mock(() => Promise.resolve("https://google.com/login")),
    callbackCodeQueryOptions: mock((provider: string, code: string) => ({
      queryKey: ["callback", provider, code],
      queryFn: () => Promise.resolve({
        access_token: "mock-token",
        user: {
          uuid: "1",
          email: "test@example.com",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      }),
    })),
  }));

  // Mock environments utils
  void mock.module("@/src/utils/environments", () => ({
    environmentsQueryOptions: mock(() => ({
      queryKey: ["environments"],
      queryFn: () => Promise.resolve([]),
      enabled: false,
    })),
  }));

  // Mock feature access
  void mock.module("@/src/hooks/use-featureaccess", () => ({
    useFeatureAccess: mock(() => ({
      annotations: false,
      search: false,
      advancedSearch: false,
    })),
  }));

  // Mock user consent mutations
  void mock.module("@/src/utils/user_consents", () => ({
    useCreateUserConsentMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateUserConsentMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
  }));

  // Mock projects, spans, and functions queries
  void mock.module("@/src/utils/projects", () => ({
    projectQueryOptions: mock(() => ({
      queryKey: ["project"],
      queryFn: () => Promise.resolve({
        uuid: "test-project-uuid",
        name: "Test Project",
        created_at: new Date().toISOString(),
      }),
    })),
    projectsQueryOptions: mock(() => ({
      queryKey: ["projects"],
      queryFn: () => Promise.resolve([]),
    })),
    useCreateProjectMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useDeleteProjectMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateProjectMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
  }));

  void mock.module("@/src/utils/spans", () => ({
    aggregatesByProjectQueryOptions: mock(() => ({
      queryKey: ["aggregates"],
      queryFn: () => Promise.resolve([
        {
          total_cost: 0.001,
          total_input_tokens: 100,
          total_output_tokens: 50,
          span_count: 5,
          start_date: new Date().toISOString(),
          average_duration_ms: 1000,
        },
      ]),
    })),
    aggregatesByFunctionQueryOptions: mock(() => ({
      queryKey: ["aggregatesByFunction"],
      queryFn: () => Promise.resolve([]),
    })),
    useUpdateSpanMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    spansSearchQueryOptions: mock(() => ({
      queryKey: ["spansSearch"],
      queryFn: () => Promise.resolve({ traces: [], count: 0 }),
    })),
    fetchSpan: mock(() => Promise.resolve({
      uuid: "test-span-uuid",
      name: "test-span",
      project_uuid: "test-project-uuid",
      created_at: new Date().toISOString(),
      data: {
        attributes: {
          function_name: "test_function",
          function_version: "1.0.0",
        },
      },
    })),
    spanQueryOptions: mock(() => ({
      queryKey: ["span"],
      queryFn: () => Promise.resolve({
        uuid: "test-span-uuid",
        span_id: "test-span-id",
        name: "test-span",
        project_uuid: "test-project-uuid",
        created_at: new Date().toISOString(),
        messages: [],
        tags: [],
        data: {
          attributes: {
            function_name: "test_function",
            function_version: "1.0.0",
          },
        },
      }),
    })),
    useDeleteSpanMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    spansQueryOptions: mock(() => ({
      queryKey: ["spans"],
      queryFn: () => Promise.resolve([]),
    })),
    fetchSpansByFunctionUuidPaged: mock(() => Promise.resolve({
      spans: [],
      total_count: 0,
    })),
  }));

  void mock.module("@/src/utils/functions", () => ({
    functionsQueryOptions: mock(() => ({
      queryKey: ["functions"],
      queryFn: () => Promise.resolve([]),
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
    functionsByNameQueryOptions: mock(() => ({
      queryKey: ["functionsByName"],
      queryFn: () => Promise.resolve([{
        uuid: "test-function-uuid",
        name: "test_function",
        version_num: 1,
        project_uuid: "test-project-uuid",
        created_at: new Date().toISOString(),
      }]),
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
  }));

  void mock.module("@/src/hooks/use-project-aggregates", () => ({
    useProjectAggregates: mock(() => ({
      data: [],
      consolidatedData: {},
      functionAggregates: {},
    })),
  }));

  // Mock settings and users queries
  void mock.module("@/src/utils/settings", () => ({
    settingsQueryOptions: mock(() => ({
      queryKey: ["settings"],
      queryFn: () => Promise.resolve({ experimental: true }),
    })),
  }));

  void mock.module("@/src/utils/users", () => ({
    userQueryOptions: mock(() => ({
      queryKey: ["user"],
      queryFn: () => Promise.resolve({
        uuid: "1",
        email: "test@example.com",
        active_organization_uuid: "org-1",
        user_organizations: [{
          organization_uuid: "org-1",
          organization: {
            uuid: "org-1",
            name: "Test Organization",
          },
          role: "OWNER",
        }],
      }),
    })),
    useCreateUserOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateActiveOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateUserOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    usersByOrganizationQueryOptions: mock(() => ({
      queryKey: ["usersByOrganization"],
      queryFn: () => Promise.resolve([]),
    })),
    useUpdateUserKeysMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useDeleteUserOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    fetchUsersByOrganization: mock(() => Promise.resolve([])),
  }));

  // Mock traces
  void mock.module("@/src/utils/traces", () => ({
    rootTraceQueryOptions: mock(() => ({
      queryKey: ["rootTrace"],
      queryFn: () => Promise.resolve({
        span_id: "test-span-id",
        uuid: "test-root-trace-uuid",
        name: "root-trace",
        project_uuid: "test-project-uuid",
        created_at: new Date().toISOString(),
        data: {
          attributes: {
            function_name: "root_function",
            function_version: "1.0.0",
          },
        },
      }),
    })),
    tracesInfiniteQueryOptions: mock(() => ({
      queryKey: ["tracesInfinite"],
      queryFn: () => Promise.resolve({
        traces: [],
        count: 0,
      }),
    })),
  }));

  // Mock organizations
  void mock.module("@/src/utils/organizations", () => ({
    organizationInviteQueryOptions: mock(() => ({
      queryKey: ["organizationInvite"],
      queryFn: () => Promise.resolve({
        uuid: "invite-uuid",
        organization: {
          uuid: "org-uuid",
          name: "Test Organization",
        },
        inviter: {
          uuid: "inviter-uuid",
          email: "inviter@example.com",
        },
      }),
    })),
    useCreateOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useDeleteOrganizationInviteMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useCreateOrganizationInviteMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    organizationInvitesQueryOptions: mock(() => ({
      queryKey: ["organizationInvites"],
      queryFn: () => Promise.resolve([]),
    })),
    useDeleteOrganizationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
  }));

  // Mock tags
  void mock.module("@/src/utils/tags", () => ({
    tagsQueryOptions: mock(() => ({
      queryKey: ["tags"],
      queryFn: () => Promise.resolve([]),
    })),
    tagsByProjectsQueryOptions: mock(() => ({
      queryKey: ["tagsByProject"],
      queryFn: () => Promise.resolve([]),
    })),
    useCreateTagMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateTagMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useDeleteTagMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
  }));

  // Mock comments
  void mock.module("@/src/utils/comments", () => ({
    commentsBySpanQueryOptions: mock(() => ({
      queryKey: ["commentsBySpan"],
      queryFn: () => Promise.resolve([]),
    })),
    useCreateCommentMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateCommentMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useDeleteCommentMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    fetchCommentsBySpan: mock(() => Promise.resolve([])),
  }));

  // Mock annotations (EE feature)
  void mock.module("@/src/ee/utils/annotations", () => ({
    annotationsByProjectQueryOptions: mock(() => ({
      queryKey: ["annotationsByProject"],
      queryFn: () => Promise.resolve([]),
    })),
    annotationsBySpanQueryOptions: mock(() => ({
      queryKey: ["annotationsBySpan"],
      queryFn: () => Promise.resolve([]),
    })),
    annotationMetricsByFunctionQueryOptions: mock(() => ({
      queryKey: ["annotationMetricsByFunction"],
      queryFn: () => Promise.resolve({}),
    })),
    annotationsByFunctionQueryOptions: mock(() => ({
      queryKey: ["annotationsByFunction"],
      queryFn: () => Promise.resolve([]),
    })),
    useCreateAnnotationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useUpdateAnnotationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useDeleteAnnotationMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
    useCreateAnnotationsMutation: mock(() => ({
      mutateAsync: mock(() => Promise.resolve({})),
      isPending: false,
    })),
  }));

  // Mock EE organizations (license info)
  void mock.module("@/src/ee/utils/organizations", () => ({
    licenseQueryOptions: mock(() => ({
      queryKey: ["license"],
      queryFn: () => Promise.resolve({
        is_valid: true,
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        features: ["annotations", "search"],
      }),
    })),
  }));

  // Mock dates utilities
  void mock.module("@/src/utils/dates", () => ({
    diffDays: mock(() => 30),
  }));

  // Mock PostHog
  void mock.module("posthog-js/react", () => ({
    usePostHog: mock(() => ({
      identify: mock(() => {}),
      capture: mock(() => {}),
      get_distinct_id: mock(() => "test-distinct-id"),
    })),
  }));

  // Set test environment
  process.env.NODE_ENV = "test";
};

// Call this in beforeAll of your test files
export const setupTestEnvironment = () => {
  setupCommonMocks();
  
  // Clear localStorage
  localStorage.clear();
  
  // Suppress console warnings in tests (optional)
  const originalConsoleWarn = console.warn;
  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      (args[0].includes("useRouter must be used inside") ||
       args[0].includes("Warning:"))
    ) {
      return;
    }
    originalConsoleWarn(...args);
  };
};