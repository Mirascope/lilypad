import { Font, useFont } from "@/src/components/FontProvider";
import { Button } from "@/src/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/src/components/ui/tooltip";

const FontTooltipOption = ({
  name,
  tooltipContent,
  active,
  onClick,
}: {
  name: string;
  tooltipContent: string;
  active: boolean;
  onClick: () => void;
}) => {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant={active ? "default" : "ghost"}
          size="sm"
          className="professional flex items-center gap-1"
          onClick={onClick}
        >
          <span className={name.toLowerCase()}>{name}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltipContent}</p>
      </TooltipContent>
    </Tooltip>
  );
};

interface FontOption {
  name: string;
  value: Font;
  tooltipContent?: string;
}
export const FontToggle = () => {
  const { setFont, font } = useFont();

  // Array of font options to render
  const fontOptions: FontOption[] = [
    {
      name: "Default",
      value: "default",
      tooltipContent: "A mixture of professional and fun fonts.",
    },
    {
      name: "Professional",
      value: "professional",
      tooltipContent: "A Clean, consistent typeface.",
    },
    { name: "Fun", value: "fun", tooltipContent: "William's Handwriting." },
  ];

  return (
    <div className="inline-flex w-fit items-center gap-1 rounded-lg bg-muted p-1">
      {fontOptions.map((option) => (
        <FontTooltipOption
          key={option.value}
          name={option.name}
          tooltipContent={option.tooltipContent ?? ""}
          active={font === option.value}
          onClick={() => setFont(option.value)}
        />
      ))}
    </div>
  );
};
