import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronRight } from "lucide-react";
import { ReactNode } from "react";

export const CollapsibleCard = ({
  title,
  content,
}: {
  title: ReactNode;
  content: ReactNode;
}) => {
  return (
    <Collapsible>
      <Card className="border rounded-lg">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg font-medium">
            <CollapsibleTrigger className="data-[state=open]:rotate-90 transition-transform duration-200">
              <ChevronRight className="h-5 w-5 text-primary hover:text-primary/80" />
            </CollapsibleTrigger>
            {title}
          </CardTitle>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="pt-0 whitespace-pre-wrap text-sm">
            <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg border shadow-sm overflow-x-auto">
              {content}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
};
