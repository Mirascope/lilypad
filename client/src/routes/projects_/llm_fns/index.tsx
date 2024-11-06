import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/projects/llm_fns/")({
  component: () => <div>Hello /projects/llm_fn/!</div>,
});
