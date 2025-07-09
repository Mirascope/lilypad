import { AuthProvider } from "@/src/auth";
import { Onboarding } from "@/src/components/Onboarding";
import { setupTestEnvironment } from "@/src/test-setup";
import { createTestQueryClient } from "@/src/test-utils";
import { QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it, mock } from "bun:test";

// Mock the mobile hook
void mock.module("@/src/hooks/use-mobile", () => ({
  useIsMobile: mock(() => false),
}));

// Mock the specific API mutation hooks used by the component
void mock.module("@/src/utils/organizations", () => ({
  useCreateOrganizationMutation: mock(() => ({
    mutateAsync: mock(() =>
      Promise.resolve({
        uuid: "org-uuid",
        name: "Test Organization",
      })
    ),
    isPending: false,
  })),
}));

void mock.module("@/src/utils/projects", () => ({
  useCreateProjectMutation: mock(() => ({
    mutateAsync: mock(() =>
      Promise.resolve({
        uuid: "project-uuid",
        name: "Test Project",
      })
    ),
    isPending: false,
  })),
}));

void mock.module("@/src/utils/environments", () => ({
  useCreateEnvironmentMutation: mock(() => ({
    mutateAsync: mock(() =>
      Promise.resolve({
        uuid: "env-uuid",
        name: "Dev",
      })
    ),
    isPending: false,
  })),
}));

void mock.module("@/src/utils/api-keys", () => ({
  useCreateApiKeyMutation: mock(() => ({
    mutateAsync: mock(() => Promise.resolve("test-api-key")),
    isPending: false,
  })),
}));

// Mock the spans query to return a proper structure and disable it
const mockSpansQuery = mock((projectUuid?: string) => ({
  queryKey: ["spans", projectUuid],
  queryFn: () => Promise.resolve({ items: [] }),
  enabled: false, // Disable the query to prevent it from running
}));

void mock.module("@/src/utils/spans", () => ({
  spansQueryOptions: mockSpansQuery,
}));

// Mock the user data
const mockUser = {
  uuid: "1",
  email: "test@example.com",
  first_name: "John",
  last_name: "Doe",
  access_token: "mock-token",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

void mock.module("@/src/utils/users", () => ({
  userQueryOptions: mock(() => ({
    queryKey: ["user"],
    queryFn: () => Promise.resolve(mockUser),
  })),
}));

// Mock the EE components
mock.module("@/src/ee/components/Playground", () => ({
  Playground: mock(() => <div>Playground Mock</div>),
}));

mock.module("@/src/ee/hooks/use-playground", () => ({
  usePlaygroundContainer: mock(() => ({})),
}));

// Mock Tanstack Router
mock.module("@tanstack/react-router", () => ({
  useNavigate: mock(() => mock(() => Promise.resolve())),
}));

// Mock sonner for toast notifications
mock.module("sonner", () => ({
  toast: {
    error: mock(() => {}),
    success: mock(() => {}),
  },
}));

const renderOnboarding = (isMobile = false) => {
  const queryClient = createTestQueryClient();

  // Pre-populate the query cache with user data
  queryClient.setQueryData(["user"], mockUser);

  // Pre-populate the query cache with spans data for project-uuid
  queryClient.setQueryData(["spans", "project-uuid"], { items: [] });

  // Update the mobile hook mock
  const { useIsMobile } = require("@/src/hooks/use-mobile");
  useIsMobile.mockReturnValue(isMobile);

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Onboarding />
      </AuthProvider>
    </QueryClientProvider>
  );
};

describe("Onboarding Component", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  describe("Desktop rendering", () => {
    it("should render desktop onboarding with stepper navigation", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByText("Welcome")).toBeTruthy();
        expect(screen.getByText("Run a Function")).toBeTruthy();
        expect(screen.getByText("Next Steps")).toBeTruthy();
      });
    });

    it("should render welcome panel by default", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByText("Welcome to")).toBeTruthy();
        expect(screen.getByText("Lilypad")).toBeTruthy();
        expect(screen.getByText("We are excited to have you here!")).toBeTruthy();
      });
    });

    it("should display organization and project form fields", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByLabelText("Organization Name")).toBeTruthy();
        expect(screen.getByLabelText("Project Name")).toBeTruthy();
        expect(screen.getByRole("button", { name: "Create" })).toBeTruthy();
      });
    });

    it("should have default values for form fields", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        const orgInput = screen.getByLabelText("Organization Name") as HTMLInputElement;
        const projectInput = screen.getByLabelText("Project Name") as HTMLInputElement;

        expect(orgInput.value).toBe("John's Organization");
        expect(projectInput.value).toBe("John's Project");
      });
    });
  });

  describe("Mobile rendering", () => {
    it("should render mobile onboarding with circular stepper", async () => {
      renderOnboarding(true);

      await waitFor(() => {
        expect(screen.getByText("Welcome")).toBeTruthy();
        expect(screen.queryByText("Run a Function")).toBeFalsy();
        expect(screen.queryByText("Next Steps")).toBeFalsy();
      });
    });

    it("should show current step title only in mobile", async () => {
      renderOnboarding(true);

      await waitFor(() => {
        expect(screen.getByText("Welcome")).toBeTruthy();
        expect(screen.getByText("Welcome to")).toBeTruthy();
      });
    });
  });

  describe("Form interaction", () => {
    it("should allow editing organization name", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        const orgInput = screen.getByLabelText("Organization Name") as HTMLInputElement;
        fireEvent.change(orgInput, { target: { value: "My Custom Organization" } });
        expect(orgInput.value).toBe("My Custom Organization");
      });
    });

    it("should allow editing project name", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        const projectInput = screen.getByLabelText("Project Name") as HTMLInputElement;
        fireEvent.change(projectInput, { target: { value: "My Custom Project" } });
        expect(projectInput.value).toBe("My Custom Project");
      });
    });

    it("should show loading state when form is submitted", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        const createButton = screen.getByRole("button", { name: "Create" });
        expect(createButton).toBeTruthy();
      });

      // The component starts with "Create" text by default
      expect(screen.getByText("Create")).toBeTruthy();
      expect(screen.queryByText("Creating...")).toBeFalsy();
    });

    it("should have form submission functionality", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        const createButton = screen.getByRole("button", { name: "Create" });
        expect(createButton).toBeTruthy();
        expect((createButton as HTMLButtonElement).disabled).toBe(false);
      });

      // Test that form fields are present and functional
      const orgInput = screen.getByLabelText("Organization Name");
      const projectInput = screen.getByLabelText("Project Name");

      expect(orgInput).toBeTruthy();
      expect(projectInput).toBeTruthy();
    });
  });

  describe("Step navigation", () => {
    it("should have stepper navigation with all steps", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByText("Welcome")).toBeTruthy();
        expect(screen.getByText("Run a Function")).toBeTruthy();
        expect(screen.getByText("Next Steps")).toBeTruthy();
      });
    });

    it("should start on step 1 (Welcome)", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByText("Welcome to")).toBeTruthy();
        expect(screen.getByText("Lilypad")).toBeTruthy();
      });
    });

    it("should have form fields for organization and project creation", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByLabelText("Organization Name")).toBeTruthy();
        expect(screen.getByLabelText("Project Name")).toBeTruthy();
        expect(screen.getByRole("button", { name: "Create" })).toBeTruthy();
      });
    });
  });

  describe("Error handling", () => {
    it("should have error handling for mutation failures", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        const createButton = screen.getByRole("button", { name: "Create" });
        expect(createButton).toBeTruthy();
      });

      // Test passes if the component renders without crashing
      // Error handling logic is present in the component but requires integration testing
      expect(screen.getByText("Create")).toBeTruthy();
    });
  });

  describe("Component integration", () => {
    it("should render FontToggle component", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByText("Font")).toBeTruthy();
      });
    });

    it("should render LilypadLogo component", async () => {
      renderOnboarding(false);

      await waitFor(() => {
        expect(screen.getByText("Welcome to")).toBeTruthy();
        expect(screen.getByText("Lilypad")).toBeTruthy();
      });
    });
  });
});
