import { createFileRoute, useParams } from "@tanstack/react-router";
import { LLMFunction } from "@/components/LLMFunction";
import { EditorForm, EditorFormValues } from "@/components/EditorForm";
import { useRef, useState } from "react";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { LexicalEditor } from "lexical";
import { SubmitHandler } from "react-hook-form";
import { CallArgsCreate } from "@/types/types";
import { Typography } from "@/components/ui/typography";
import { CreateEditorForm } from "@/components/CreateEditorForm";
export const Route = createFileRoute("/projects/$projectId/llmFns/")({
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
