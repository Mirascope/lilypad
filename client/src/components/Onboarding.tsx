import { CopyKeyContent } from "@/components/apiKeys/CreateAPIKeyDialog";
import { CodeSnippet } from "@/components/CodeSnippet";
import { LilypadIcon } from "@/components/LilypadIcon";
import { NotFound } from "@/components/NotFound";
import { defineStepper } from "@/components/stepper";
import { TabGroup } from "@/components/TabGroup";
import { Button } from "@/components/ui/button";
import { DialogClose } from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import { Playground } from "@/ee/components/Playground";
import { usePlaygroundContainer } from "@/ee/hooks/use-playground";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { OrganizationCreate, ProjectCreate } from "@/types/types";
import { useCreateApiKeyMutation } from "@/utils/api-keys";
import { useCreateEnvironmentMutation } from "@/utils/environments";
import { useCreateOrganizationMutation } from "@/utils/organizations";
import { useCreateProjectMutation } from "@/utils/projects";
import { spansQueryOptions } from "@/utils/spans";
import { userQueryOptions } from "@/utils/users";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";
import { JSX, ReactNode, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

const stepper = defineStepper(
  { id: "step-1", title: "Welcome" },
  { id: "step-2", title: "Run a Function" },
  { id: "step-3", title: "Next Steps" }
);

const { Stepper, useStepper } = stepper;

interface StepperPanelProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

const StepperPanel = ({
  title,
  description,
  children,
  className,
}: StepperPanelProps) => {
  return (
    <Stepper.Panel
      className={cn(`w-full h-full flex-1 flex flex-col p-4`, className)}
    >
      <Typography variant="h3" className="flex gap-1 items-center shrink-0">
        <LilypadIcon className="size-16" />
        {title}
      </Typography>
      {description && (
        <Typography variant="span" affects="small" className="shrink-0">
          {description}
        </Typography>
      )}
      {children}
    </Stepper.Panel>
  );
};

const OnboardingDesktop = () => {
  return (
    <Stepper.Provider
      className={cn("flex flex-col h-full w-full overflow-hidden gap-2")}
      variant={"horizontal"}
      tracking={true}
    >
      {({ methods }) => (
        <>
          <Stepper.Navigation className={"max-w-full overflow-x-auto shrink-0"}>
            {methods.all.map((step) => (
              <Stepper.Step key={step.id} of={step.id}>
                <Stepper.Title className={"text-xs"}>
                  {step.title}
                </Stepper.Title>
              </Stepper.Step>
            ))}
          </Stepper.Navigation>
          <div className="flex-1 overflow-hidden min-h-0 flex flex-col">
            {renderStepPanel(methods)}
          </div>
        </>
      )}
    </Stepper.Provider>
  );
};
const OnboardingMobile = () => {
  return (
    <Stepper.Provider className="space-y-4" variant="circle">
      {({ methods }) => (
        <>
          <Stepper.Navigation>
            <Stepper.Step of={methods.current.id}>
              <Stepper.Title>{methods.current.title}</Stepper.Title>
            </Stepper.Step>
          </Stepper.Navigation>
          {methods.when(methods.current.id, () => renderStepPanel(methods))}
        </>
      )}
    </Stepper.Provider>
  );
};
export const Onboarding = () => {
  const isMobile = useIsMobile();

  return <>{isMobile ? <OnboardingMobile /> : <OnboardingDesktop />}</>;
};
type StepperMethods = ReturnType<typeof stepper.useStepper>;
// Helper function to render the appropriate panel based on current step
const renderStepPanel = (methods: StepperMethods) => {
  switch (methods.current.id) {
    case "step-1":
      return <LilypadWelcome />;
    case "step-2":
      return <OnboardRunFunction />;
    case "step-3":
      return <OnboardNextSteps />;
  }
};

const LilypadWelcome = () => {
  return (
    <StepperPanel
      title="Welcome to Lilypad"
      className="welcome-panel flex flex-col gap-4"
    >
      <Typography variant="span" affects="small">
        We are excited to have you here!
      </Typography>
      <Typography variant="span" affects="small">
        Lilypad is a platform that enables seamless collaboration between
        developers, business users, and domain experts while maintaining quality
        and reproducibility in your AI applications.
      </Typography>
      <LilypadOnboarding />
    </StepperPanel>
  );
};

const OnboardNextSteps = () => {
  const navigate = useNavigate();
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-2");
  const handleViewTrace = () => {
    navigate({
      to: `/projects/${metadata?.project.uuid}/traces`,
    }).catch(() => toast.error("Failed to navigate to traces"));
  };

  const handleReadDocs = () => {
    window.open("https://beta.mirascope.com/docs/lilypad", "_blank");
  };

  return (
    <StepperPanel
      title="Next Steps"
      description="Congratulations! You have successfully traced your first function."
    >
      <div className="flex flex-col gap-4">
        <Typography variant="span" affects="small" className="block mb-2">
          You can now:
        </Typography>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DialogClose asChild>
            <div
              onClick={handleViewTrace}
              className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors shadow-sm flex flex-col"
            >
              <div className="font-medium mb-2">View your trace</div>
              <p className="text-sm text-gray-600">
                View the trace of your function
              </p>
            </div>
          </DialogClose>

          <div
            onClick={handleReadDocs}
            className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors shadow-sm flex flex-col"
          >
            <div className="font-medium mb-2 flex items-center">
              Read documentation
              <ExternalLink className="ml-1 h-4 w-4 text-gray-500" />
            </div>
            <p className="text-sm text-gray-600">Learn more about Lilypad</p>
          </div>
        </div>
        <DialogClose asChild>
          <Button>Close</Button>
        </DialogClose>
      </div>
    </StepperPanel>
  );
};

interface LilypadOnboardingFormValues {
  organization: OrganizationCreate;
  project: ProjectCreate;
}
const LilypadOnboarding = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const stepperMethods = useStepper();
  const methods = useForm<LilypadOnboardingFormValues>({
    defaultValues: {
      organization: {
        name: `${user.first_name}'s Organization`,
      },
      project: {
        name: `${user.first_name}'s Project`,
      },
    },
  });
  const createOrganization = useCreateOrganizationMutation();
  const createProject = useCreateProjectMutation();
  const createEnvironment = useCreateEnvironmentMutation();
  const createApiKey = useCreateApiKeyMutation();
  const handleSubmit = async (data: LilypadOnboardingFormValues) => {
    const organization = await createOrganization
      .mutateAsync(data.organization)
      .catch(() => {
        toast.error("Failed to create organization");
        return;
      });
    const project = await createProject.mutateAsync(data.project).catch(() => {
      toast.error("Failed to create project");
      return;
    });
    const environment = await createEnvironment
      .mutateAsync({
        name: "Default Environment",
        description: "Default environment for your project",
        is_default: true,
      })
      .catch(() => {
        toast.error("Failed to create environment");
        return;
      });
    if (!project || !environment || !organization) return;
    const newApiKey = await createApiKey.mutateAsync({
      name: "Default API Key",
      project_uuid: project.uuid,
      environment_uuid: environment.uuid,
    });
    stepperMethods.setMetadata("step-2", {
      apiKey: newApiKey,
      project: project,
    });
    toast.success("Organization and project created");
    methods.reset();
    stepperMethods.next();
  };
  return (
    <Form {...methods}>
      <form className="space-y-6" onSubmit={methods.handleSubmit(handleSubmit)}>
        <FormField
          control={methods.control}
          name="organization.name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Organization Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          control={methods.control}
          name="project.name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <div className="flex justify-end">
          <Button
            key="submit"
            type="submit"
            disabled={methods.formState.isSubmitting}
          >
            {methods.formState.isSubmitting ? "Creating..." : "Create"}
          </Button>
        </div>
      </form>
    </Form>
  );
};

const OnboardPlayground = () => {
  const playgroundContainer = usePlaygroundContainer({
    version: null,
  });
  return (
    <Playground version={null} playgroundContainer={playgroundContainer} />
  );
};
const OnboardCodeSnippet = () => {
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-2");
  return (
    <CodeSnippet
      code={`import os

import lilypad
from mirascope import llm, prompt_template

os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

lilypad.configure(
    auto_llm=True,
    project_id="${metadata?.project.uuid}",
    api_key="${metadata?.apiKey}",
)


@lilypad.trace(versioning="automatic")
@llm.call(provider="google", model="gemini-2.5-flash-preview-04-17")
@prompt_template("Answer this question: {question}")
def answer_question(question: str): ...


answer_question("What is the capital of France?")
`}
    />
  );
};

const OnboardCreateAPIKey = () => {
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-2");
  if (!metadata) {
    return <NotFound />;
  }
  return (
    <>
      {!metadata.apiKey ? (
        <div>Generating API Key</div>
      ) : (
        <CopyKeyContent
          apiKey={metadata.apiKey}
          projectUuid={metadata?.project.uuid}
        />
      )}
    </>
  );
};

interface Tab {
  label: string;
  value: string;
  component?: JSX.Element | null;
  isDisabled?: boolean;
}

const OnboardInstallLilypad = () => {
  const tabs: Tab[] = [
    {
      label: "pip",
      value: "pip",
      component: <CodeSnippet code={`pip install "lilypad-sdk[google]"`} />,
    },
    {
      label: "uv",
      value: "uv",
      component: <CodeSnippet code={`uv add "lilypad-sdk[google]"`} />,
    },
  ];
  return <TabGroup tabs={tabs} className="shrink-0 h-auto" />;
};

const OnboardRunLilypad = () => {
  const tabs: Tab[] = [
    {
      label: "Function",
      value: "function",
      component: <OnboardCodeSnippet />,
    },
    {
      label: "Playground",
      value: "playground",
      component: <OnboardPlayground />,
      isDisabled: true,
    },
  ];
  return <TabGroup tabs={tabs} className="flex-1 min-h-0 h-full" />;
};
const OnboardRunFunction = () => {
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-2");
  const { data: traces } = useQuery({
    ...spansQueryOptions(metadata?.project.uuid as string),
    refetchInterval: 1000,
  });
  useEffect(() => {
    if (traces?.items.length) {
      stepperMethods.next();
    }
  }, [traces?.items.length]);
  return (
    <StepperPanel
      title="Run a function"
      description="Now run a function and observe the results. You can use the API key and Project ID you just created to authenticate your requests."
      className="gap-2"
    >
      <OnboardCreateAPIKey />
      <Typography variant="h5" className="block">
        Replace `google` with any provider, `openai`, `anthropic`, etc.
      </Typography>
      <OnboardInstallLilypad />
      <Typography variant="h5" className="block">
        Copy the code below or run your own function
      </Typography>
      <OnboardRunLilypad />
    </StepperPanel>
  );
};
