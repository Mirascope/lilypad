import { CopyKeyContent } from "@/components/apiKeys/CreateAPIKeyDialog";
import { CodeSnippet } from "@/components/CodeSnippet";
import { defineStepper } from "@/components/stepper";
import { Button } from "@/components/ui/button";
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
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { JSX, ReactNode, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

const stepper = defineStepper(
  { id: "step-1", title: "Welcome" },
  { id: "step-2", title: "Function" },
  { id: "step-3", title: "Trace" }
);

const { Stepper, useStepper } = stepper;

// Reusable Panel component
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
      <Typography variant='h4'>{title}</Typography>
      {description && (
        <p className='text-sm text-slate-500 mt-2'>{description}</p>
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
          <Stepper.Navigation
            className={"max-w-full overflow-x-auto flex-shrink-0"}
          >
            {methods.all.map((step) => (
              <Stepper.Step key={step.id} of={step.id}>
                <Stepper.Title className={"text-xs"}>
                  {step.title}
                </Stepper.Title>
              </Stepper.Step>
            ))}
          </Stepper.Navigation>
          <div className='flex-1 overflow-hidden min-h-0 flex flex-col'>
            {renderStepPanel(methods)}
          </div>
        </>
      )}
    </Stepper.Provider>
  );
};
const OnboardingMobile = () => {
  return (
    <Stepper.Provider className='space-y-4' variant='circle'>
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
    <div className='flex flex-col h-full'>
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
    default:
      return null;
  }
};

const LilypadWelcome = () => {
  return (
    <StepperPanel title='Welcome to Lilypad' className='welcome-panel'>
      <p>We are excited to have you here!</p>
      <p className='text-sm text-slate-500 mt-4'>
        Lilypad is a platform that enables seamless collaboration between
        developers, business users, and domain experts while maintaining quality
        and reproducibility in your AI applications.
      </p>
      <LilypadOnboarding />
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
  const handleSubmit = async (data: LilypadOnboardingFormValues) => {
    await createOrganization.mutateAsync(data.organization).catch(() => {
      toast.error("Failed to create organization");
    });
    const project = await createProject.mutateAsync(data.project).catch(() => {
      toast.error("Failed to create project");
    });
    const environment = await createEnvironment
      .mutateAsync({
        name: "Default Environment",
        description: "Default environment for your project",
        is_default: true,
      })
      .catch(() => toast.error("Failed to create environment"));
    stepperMethods.setMetadata("step-2", {
      project: project,
      environment: environment,
    });
    toast.success("Organization and project created");
    methods.reset();
    stepperMethods.next();
  };
  return (
    <Form {...methods}>
      <form className='space-y-6' onSubmit={methods.handleSubmit(handleSubmit)}>
        <FormField
          control={methods.control}
          name='organization.name'
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
          name='project.name'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <div className='flex justify-end'>
          <Button
            key='submit'
            type='submit'
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
    <div className='flex flex-col overflow-auto'>
      <Typography variant={"span"} affects='small' className='block mb-2'>
        Copy the code below or run your own function
      </Typography>
      <CodeSnippet
        className='w-full flex-1'
        code={`import os
import lilypad

os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

lilypad.configure(
    project_id="${metadata?.projectUuid ?? "YOUR_PROJECT_ID"}",
    api_key="${metadata?.apiKey ?? "YOUR_API_KEY"}"
)

@lilypad.trace(versioning="automatic")
@google.call("gemini-2.5-flash-preview-04-17")
@prompt_template("Answer this question: {question}")
def answer_question(question: str): ...

response = answer_question("What is the capital of France?")`}
      />
    </div>
  );
};
const OnboardCreateAPIKey = () => {
  const createApiKey = useCreateApiKeyMutation();
  const stepperMethods = useStepper();
  const metadata = stepperMethods.getMetadata("step-2");
  const [apiKey, setApiKey] = useState<string | null>(null);
  useEffect(() => {
    if (apiKey) return;

    const getApiKey = async () => {
      const newApiKey = await createApiKey.mutateAsync({
        name: "Default API Key",
        project_uuid: metadata?.project.uuid,
        environment_uuid: metadata?.environment.uuid,
      });
      setApiKey(newApiKey);
      stepperMethods.setMetadata("step-3", {
        apiKey: newApiKey,
        projectUuid: metadata?.project.uuid,
      });
    };
    getApiKey().catch(() => toast.error("Failed to create API key"));
  }, [apiKey]);
  return (
    <>
      {!apiKey ? (
        <div>Generating API Key</div>
      ) : (
        <CopyKeyContent apiKey={apiKey} projectUuid={metadata?.project.uuid} />
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
const OnboardRunFunction = () => {
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
    <StepperPanel
      title='Run a function'
      description='Now run a function and observe the results. You can use the API key and Project ID you just created to authenticate your requests.'
    >
      <div className='flex flex-col h-full'>
        <OnboardCreateAPIKey />
        <Tabs
          value={tab}
          onValueChange={(value) => setTab(value)}
          className='w-full flex-1 min-h-0 flex flex-col'
        >
          <div>
            <div className='flex justify-center w-full'>
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
            <Separator className='my-2' />
          </div>

          <div className='flex-1 min-h-0 relative'>
            {tabs.map((tab) => (
              <TabsContent
                key={tab.value}
                value={tab.value}
                className='absolute inset-0 min-h-0 overflow-auto'
              >
                {tab.component}
              </TabsContent>
            ))}
          </div>
        </Tabs>
      </div>
    </StepperPanel>
  );
};
