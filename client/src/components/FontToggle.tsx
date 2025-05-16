import { useFont } from "@/components/FontProvider";
import { Button } from "@/components/ui/button";
export const FontToggle = () => {
  const { setFont, font } = useFont();
  return (
    <div className="inline-flex items-center p-1 gap-1 rounded-lg bg-muted w-fit">
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
