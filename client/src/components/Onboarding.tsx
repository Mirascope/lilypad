import { CopyKeyContent } from "@/components/apiKeys/CreateAPIKeyDialog";
import { CodeSnippet } from "@/components/CodeSnippet";
import { NotFound } from "@/components/NotFound";
import { defineStepper } from "@/components/stepper";
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
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { JSX, ReactNode, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

// TODO: Review onboarding
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
      className={cn(
        `w-full overflow-auto flex-1 min-h-0 max-h-full
        rounded border bg-primary/5 p-8`,
        className
      )}
    >
      <Typography variant="h4">{title}</Typography>
      {description && (
        <p className="text-sm text-slate-500 mt-2">{description}</p>
      )}
      {children}
    </Stepper.Panel>
  );
};

const OnboardingDesktop = () => {
  return (
    <Stepper.Provider
      className={cn("flex flex-col h-full w-full overflow-hidden")}
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

  return (
    <div className="flex flex-col h-full">
      {isMobile ? <OnboardingMobile /> : <OnboardingDesktop />}
    </div>
  );
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
    <StepperPanel title="Welcome to Lilypad" className="welcome-panel">
      <p>We are excited to have you here!</p>
      <p className="text-sm text-slate-500 mt-4">
        Lilypad is a platform that enables seamless collaboration between
        developers, business users, and domain experts while maintaining quality
        and reproducibility in your AI applications.
      </p>
      <LilypadOnboarding />
    </StepperPanel>
  );
};

const OnboardNextSteps = () => {
  const navigate = useNavigate();
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-3");
  const handleViewTrace = () => {
    navigate({
      to: `/projects/${metadata?.projectUuid}/traces`,
    }).catch(() => toast.error("Failed to navigate to traces"));
  };

  const handleReadDocs = () => {
    window.open("https://lilypad.so/docs", "_blank");
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
  const metadata = stepperMethods.getMetadata("step-3");
  return (
    <div className="flex flex-col">
      <Typography variant={"span"} affects="small" className="block mb-2">
        Copy the code below or run your own function
      </Typography>
      <CodeSnippet
        code={`import os

import lilypad
from mirascope import llm, prompt_template

os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

lilypad.configure(
    auto_llm=True,
    project_id="${metadata?.projectUuid}",
    api_key="${metadata?.apiKey}",
)


@lilypad.trace(versioning="automatic")
@llm.call(provider="google", model="gemini-2.5-flash-preview-04-17")
@prompt_template("Answer this question: {question}")
def answer_question(question: str): ...


answer_question("What is the capital of France?")
`}
      />
    </div>
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
      component: (
        <div className="flex flex-col min-h-20">
          <Typography variant={"span"} affects="small" className="block mb-2">
            Replace `google` with any provider, `openai`, `anthropic`, etc.
          </Typography>
          <CodeSnippet code={`pip install lilypad-python[google]`} />
        </div>
      ),
    },
    {
      label: "uv",
      value: "uv",
      component: (
        <div className="flex flex-col min-h-20">
          <Typography variant={"span"} affects="small" className="block mb-2">
            Replace `google` with any provider, `openai`, `anthropic`, etc.
          </Typography>
          <CodeSnippet code={`uv add lilypad-python[google]`} />
        </div>
      ),
    },
  ];
  const [tab, setTab] = useState<string>(tabs[0].value);
  return (
    <Tabs
      value={tab}
      onValueChange={(value) => setTab(value)}
      className="w-full shrink flex flex-col"
    >
      <div className="flex justify-center w-full">
        <TabsList className={`w-[80px]`}>
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              disabled={tab.isDisabled}
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <Separator className="my-2" />

      <div className="flex-1 min-h-20 relative">
        {tabs.map((tab) => (
          <TabsContent
            key={tab.value}
            value={tab.value}
            className="absolute inset-0"
          >
            {tab.component}
          </TabsContent>
        ))}
      </div>
    </Tabs>
  );
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
  const [tab, setTab] = useState<string>(tabs[0].value);
  return (
    <Tabs
      value={tab}
      onValueChange={(value) => setTab(value)}
      className="w-full flex-1 min-h-0 flex flex-col"
    >
      <div className="flex justify-center w-full">
        <TabsList className={`w-[180px]`}>
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              disabled={tab.isDisabled}
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <Separator className="my-2" />

      <div className="flex-1 min-h-0 relative">
        {tabs.map((tab) => (
          <TabsContent
            key={tab.value}
            value={tab.value}
            className="absolute inset-0 min-h-0 overflow-auto"
          >
            {tab.component}
          </TabsContent>
        ))}
      </div>
    </Tabs>
  );
};
const OnboardRunFunction = () => {
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-3");
  const { data: traces } = useQuery({
    ...spansQueryOptions(metadata?.projectUuid as string),
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
    >
      <div className="flex flex-col h-full">
        <OnboardCreateAPIKey />
        <OnboardInstallLilypad />
        <OnboardRunLilypad />
      </div>
    </StepperPanel>
  );
};
