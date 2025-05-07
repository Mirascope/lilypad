import { JSX } from "react";

export enum TraceTab {
  CODE = "code",
  SIGNATURE = "signature",
  OUTPUT = "output",
  METADATA = "metadata",
  DATA = "data",
}

export interface Tab {
  label: string;
  value: TraceTab;
  component?: JSX.Element | null;
}
