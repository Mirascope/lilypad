import { useFont } from "@/components/FontProvider";
import { Button } from "@/components/ui/button";
export const FontToggle = () => {
  const { setFont, font } = useFont();
  return (
    <div className="bg-muted inline-flex w-fit items-center gap-1 rounded-lg p-1">
      <Button
        variant={font === "default" ? "default" : "ghost"}
        size="sm"
        className="flex items-center gap-1"
        onClick={() => setFont("default")}
      >
        <span className="professional">Default</span>
      </Button>
      <Button
        variant={font === "professional" ? "default" : "ghost"}
        size="sm"
        className="flex items-center gap-1"
        onClick={() => setFont("professional")}
      >
        <span className="professional">Professional</span>
      </Button>
      <Button
        variant={font === "fun" ? "default" : "ghost"}
        size="sm"
        className="flex items-center gap-1"
        onClick={() => setFont("fun")}
      >
        <span className="fun">Fun</span>
      </Button>
    </div>
  );
};
