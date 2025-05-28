import { JSX, ReactNode } from "react";

export enum TraceTab {
  RESPONSE = "response",
  CONTENT = "content",
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
  ANNOTATE = "annotate",
}

export interface Tab {
  label: string | ReactNode;
  value: TraceTab | CommentTab;
  component?: JSX.Element | null;
}
