import { useAuth } from "@/src/auth";
import { CreateAPIKeyForm } from "@/src/components/apiKeys/CreateAPIKeyForm";
import { CodeBlock } from "@/src/components/code-block";
import { NotFound } from "@/src/components/NotFound";
import { Alert, AlertDescription, AlertTitle } from "@/src/components/ui/alert";
import { Button } from "@/src/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/src/components/ui/dialog";
import { PlusCircle, TriangleAlert } from "lucide-react";
import { Dispatch, ReactNode, SetStateAction, useState } from "react";

interface CreateAPIKeyDialogProps {
  trigger?: ReactNode;
}

export const CreateAPIKeyDialog = ({ trigger }: CreateAPIKeyDialogProps) => {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [projectUuid, setProjectUuid] = useState<string | null>(null);
  const { activeEnvironment } = useAuth();
  const defaultTrigger = (
    <Button
      variant="ghost"
      size="iconSm"
      className="text-primary hover:bg-background hover:text-primary/80"
    >
      <PlusCircle />
    </Button>
  );

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        {trigger ?? defaultTrigger}
      </DialogTrigger>
      <DialogContent className="max-w-md overflow-x-auto" onClick={(e) => e.stopPropagation()}>
        <DialogHeader className="shrink-0">
          <DialogTitle>Create new API Key</DialogTitle>
          <DialogDescription>Generate a Lilypad API Key for your organization.</DialogDescription>
        </DialogHeader>
        {apiKey ? (
          <CopyKeyButton
            apiKey={apiKey}
            setApiKey={setApiKey}
            projectUuid={projectUuid}
            setProjectUuid={setProjectUuid}
          />
        ) : activeEnvironment ? (
          <CreateAPIKeyForm
            setApiKey={setApiKey}
            setProjectUuid={setProjectUuid}
            defaultEnvironment={activeEnvironment}
          />
        ) : (
          <div>No environment found. Please create an environment first.</div>
        )}
      </DialogContent>
    </Dialog>
  );
};

const CopyKeyButton = ({
  apiKey,
  setApiKey,
  projectUuid,
  setProjectUuid,
}: {
  apiKey: string;
  setApiKey: Dispatch<SetStateAction<string | null>>;
  projectUuid: string | null;
  setProjectUuid: Dispatch<SetStateAction<string | null>>;
}) => {
  const handleCleanup = () => {
    setApiKey(null);
    setProjectUuid(null);
  };

  if (!projectUuid) return <NotFound />;
  return (
    <div className="max-w-full space-y-6 overflow-hidden">
      <DialogHeader className="shrink-0">
        <DialogTitle>API Key Created</DialogTitle>
        <DialogDescription className="space-y-4">
          Copy your project ID and API key into your environment
        </DialogDescription>
      </DialogHeader>
      <CopyKeyContent apiKey={apiKey} projectUuid={projectUuid} />
      <DialogFooter>
        <DialogClose asChild>
          <Button type="button" variant="outline" onClick={handleCleanup}>
            Close
          </Button>
        </DialogClose>
      </DialogFooter>
    </div>
  );
};

export const CopyKeyContent = ({
  apiKey,
  projectUuid,
}: {
  apiKey: string;
  projectUuid: string | null;
}) => {
  return (
    <div className="flex shrink-0 flex-col gap-4">
      <div className="overflow-x-auto">
        <CodeBlock
          language="bash"
          code={`LILYPAD_PROJECT_ID="${projectUuid}"
LILYPAD_API_KEY="${apiKey}"`}
          showLineNumbers={false}
        />
      </div>
      <Alert variant="destructive">
        <TriangleAlert className="h-4 w-4" />
        <AlertTitle>Warning</AlertTitle>
        <AlertDescription>You won&apos;t be able to see your API key again.</AlertDescription>
      </Alert>
    </div>
  );
};
