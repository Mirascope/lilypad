import { AnnotationLayout } from "@/src/routes/_auth/projects/$projectUuid/annotations/$";
import { renderRoute, mockAuthenticatedContext } from "@/src/test-utils";
import { setupTestEnvironment } from "@/src/test-setup";
import { screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "bun:test";

describe("AnnotationLayout", () => {
  beforeAll(() => {
    setupTestEnvironment();
  });

  it("should render annotations page", async () => {
    await renderRoute({
      path: "/_auth/projects/$projectUuid/annotations/$",
      component: AnnotationLayout,
      authContext: mockAuthenticatedContext,
      params: { projectUuid: "test-project-uuid", _splat: "" },
      initialPath: "/_auth/projects/test-project-uuid/annotations/",
    });

    // Since annotations can be empty, check for the "No Annotation Selected" state
    await waitFor(() => {
      expect(screen.getByText("No Annotation Selected")).toBeTruthy();
    });
  });
});