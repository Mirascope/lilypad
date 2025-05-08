import { JSX, ReactNode } from "react";

export enum TraceTab {
  CODE = "code",
  SIGNATURE = "signature",
  OUTPUT = "output",
  METADATA = "metadata",
  DATA = "data",
  PROMPT_TEMPLATE = "prompt_template",
  EVENTS = "events",
  MESSAGES = "messages",
}

export enum CommentTab {
  ANNOTATIONS = "annotations",
  COMMENTS = "comments",
}

export interface Tab {
  label: string | ReactNode;
  value: TraceTab | CommentTab;
  component?: JSX.Element | null;
}
