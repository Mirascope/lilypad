import { CopyButton } from "@/components/CopyButton";
import { TagPopover } from "@/components/TagPopover";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { SpanMoreDetails } from "@/types/types";

export const FunctionTitle = ({ span }: { span: SpanMoreDetails }) => {
  const spanData: Record<string, unknown> = span.data as Record<
    string,
    unknown
  >;
  const attributes: Record<string, string> | undefined =
    spanData.attributes as Record<string, string>;
  const lilypadType = attributes?.["lilypad.type"];
  const versionNum = attributes?.[`lilypad.${lilypadType}.version`];
  return (
    <div className="flex flex-col gap-1">
      <div className="flex gap-2 items-center">
        <Typography variant="h3">{span.display_name}</Typography>
        <Typography variant="span" affects="muted">
          {versionNum && `v${versionNum}`}
        </Typography>
        {span.function_uuid && <CopyButton content={span.function_uuid} />}
      </div>
      <div className="flex gap-1 flex-wrap">
        {span.tags?.map((tag) => (
          <Badge pill variant="outline" size="sm" key={tag.uuid}>
            {tag.name}
          </Badge>
        ))}
        {span.project_uuid && (
          <TagPopover
            spanUuid={span.uuid}
            projectUuid={span.project_uuid}
            key="add-tag"
          />
        )}
      </div>
    </div>
  );
};
