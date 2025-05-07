import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronRight } from "lucide-react";
import { ReactNode } from "react";

export const CollapsibleChevronTrigger = () => {
  return (
    <CollapsibleTrigger className="data-[state=open]:rotate-90 transition-transform duration-200">
      <ChevronRight className="h-5 w-5 text-primary hover:text-primary/80" />
    </CollapsibleTrigger>
  );
};
export const CollapsibleCard = ({
  title,
  content,
}: {
  title?: ReactNode;
  content: ReactNode;
}) => {
  return (
    <Collapsible>
      <Card className="border rounded-lg">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg font-medium">
            <CollapsibleChevronTrigger />
            {title}
          </CardTitle>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="pt-0 whitespace-pre-wrap text-sm">
            {content}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
};
