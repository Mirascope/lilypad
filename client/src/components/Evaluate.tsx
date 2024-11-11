import { Button } from "@/components/ui/button";
import { VersionPublic } from "@/types/types";

export const Evaluate = ({
  version,
  projectId,
}: {
  version: VersionPublic;
  projectId: number;
}) => {
  return (
    <div>
      <Button>Generate Data</Button>
    </div>
  );
};
