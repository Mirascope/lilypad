import { createFileRoute, useParams } from "@tanstack/react-router";
import { CreateEditorForm } from "@/components/CreateEditorForm";
export const Route = createFileRoute("/projects/$projectId/functions/")({
  component: () => <CreatePrompt />,
});

export const CreatePrompt = () => {
  const { projectId } = useParams({ from: Route.id });

  return (
    <>
      <CreateEditorForm
        {...{
          projectId: Number(projectId),
        }}
      />
    </>
  );
};
