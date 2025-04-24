import { CopyKeyContent } from "@/components/apiKeys/CreateAPIKeyDialog";
import { CreateAPIKeyForm } from "@/components/apiKeys/CreateAPIKeyForm";
import { CodeSnippet } from "@/components/CodeSnippet";
import { CreateEnvironmentForm } from "@/components/environments/CreateEnvironmentForm";
import { CreateOrganizationForm } from "@/components/OrganizationDialog";
import { CreateProjectForm } from "@/components/projects/CreateProjectForm";
import { defineStepper } from "@/components/stepper";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { environmentsQueryOptions } from "@/utils/environments";
import { projectsQueryOptions } from "@/utils/projects";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { CircleCheck } from "lucide-react";
import { Dispatch, ReactNode, SetStateAction, useState } from "react";

const { Stepper } = defineStepper(
  { id: "step-1", title: "Welcome" },
  { id: "step-2", title: "Organization" },
  { id: "step-3", title: "Project" },
  { id: "step-3-1", title: "Environment" },
  { id: "step-3-2", title: "API Key" },
  { id: "step-4", title: "Function" }
);

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
  const isMobile = useIsMobile();
  return (
    <Stepper.Panel
      className={cn(
        `w-full overflow-y-auto overflow-x-hidden 
        content-center rounded border bg-primary/5 p-8`,
        isMobile ? "flex-1" : "h-[500px]",
        className
      )}
    >
      <Typography variant='h4'>{title}</Typography>
      {description && (
        <p className='text-sm text-slate-500 mt-2'>{description}</p>
      )}
      <div className='w-full mt-4'>{children}</div>
    </Stepper.Panel>
  );
};

interface OnboardingProps {
  apiKey: string | null;
  projectUuid: string | null;
  setApiKey: Dispatch<SetStateAction<string | null>>;
  setProjectUuid: Dispatch<SetStateAction<string | null>>;
}
const OnboardingDesktop = ({
  apiKey,
  projectUuid,
  setApiKey,
  setProjectUuid,
}: OnboardingProps) => {
  return (
    <Stepper.Provider
      className={cn("space-y-4 max-w-full")}
      variant={"horizontal"}
      tracking={true}
    >
      {({ methods }) => (
        <>
          <Stepper.Navigation className={"max-w-full overflow-x-auto"}>
            {methods.all.map((step) => (
              <Stepper.Step
                key={step.id}
                of={step.id}
                onClick={() => methods.goTo(step.id)}
              >
                <Stepper.Title className={"text-xs"}>
                  {step.title}
                </Stepper.Title>
              </Stepper.Step>
            ))}
          </Stepper.Navigation>
          {renderStepPanel(
            methods.current.id,
            apiKey,
            projectUuid,
            setApiKey,
            setProjectUuid
          )}
          <Stepper.Controls>
            {!methods.isLast && (
              <Button
                variant='secondary'
                onClick={methods.prev}
                disabled={methods.isFirst}
              >
                Previous
              </Button>
            )}
            <Button onClick={methods.isLast ? methods.reset : methods.next}>
              {methods.isLast ? "Finish" : "Next"}
            </Button>
          </Stepper.Controls>
        </>
      )}
    </Stepper.Provider>
  );
};
const OnboardingMobile = ({
  apiKey,
  projectUuid,
  setApiKey,
  setProjectUuid,
}: OnboardingProps) => {
  return (
    <Stepper.Provider className='space-y-4' variant='circle'>
      {({ methods }) => (
        <>
          <Stepper.Navigation>
            <Stepper.Step of={methods.current.id}>
              <Stepper.Title>{methods.current.title}</Stepper.Title>
            </Stepper.Step>
          </Stepper.Navigation>
          {methods.when(methods.current.id, () =>
            renderStepPanel(
              methods.current.id,
              apiKey,
              projectUuid,
              setApiKey,
              setProjectUuid
            )
          )}
          <Stepper.Controls>
            {!methods.isLast && (
              <Button
                variant='secondary'
                onClick={methods.prev}
                disabled={methods.isFirst}
              >
                Previous
              </Button>
            )}
            <Button onClick={methods.isLast ? methods.reset : methods.next}>
              {methods.isLast ? "Reset" : "Next"}
            </Button>
          </Stepper.Controls>
        </>
      )}
    </Stepper.Provider>
  );
};
export const Onboarding = () => {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [projectUuid, setProjectUuid] = useState<string | null>(null);
  const isMobile = useIsMobile();

  return (
    <>
      {isMobile ? (
        <OnboardingMobile
          apiKey={apiKey}
          projectUuid={projectUuid}
          setApiKey={setApiKey}
          setProjectUuid={setProjectUuid}
        />
      ) : (
        <OnboardingDesktop
          apiKey={apiKey}
          projectUuid={projectUuid}
          setApiKey={setApiKey}
          setProjectUuid={setProjectUuid}
        />
      )}
    </>
  );
};

// Helper function to render the appropriate panel based on current step
const renderStepPanel = (
  stepId: string,
  apiKey: string | null,
  projectUuid: string | null,
  setApiKey: Dispatch<SetStateAction<string | null>>,
  setProjectUuid: Dispatch<SetStateAction<string | null>>
) => {
  switch (stepId) {
    case "step-1":
      return <LilypadWelcome />;
    case "step-2":
      return <OnboardCreateOrganization />;
    case "step-3":
      return <OnboardCreateProject />;
    case "step-3-1":
      return <OnboardCreateEnvironment />;
    case "step-3-2":
      return (
        <OnboardCreateAPIKey
          apiKey={apiKey}
          projectUuid={projectUuid}
          setApiKey={setApiKey}
          setProjectUuid={setProjectUuid}
        />
      );
    case "step-4":
      return <OnboardRunFunction apiKey={apiKey} projectUuid={projectUuid} />;
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
    </StepperPanel>
  );
};

const OnboardCreateOrganization = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const activeOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user.active_organization_uuid
  );

  return (
    <StepperPanel
      title='Create a new organization'
      description='Create a new organization to get started with Lilypad.'
    >
      {activeOrganization ? (
        <div className='p-6 rounded-lg border text-center'>
          <div className='flex flex-col items-center space-y-3'>
            <div className='text-blue-700 bg-blue-100 p-3 rounded-full'>
              <CircleCheck className='h-6 w-6' />
            </div>
            <h3 className='font-medium text-gray-900'>Organization Created</h3>
            <Typography variant='p' affects='muted'>
              You&apos;re a member of{" "}
              <Typography variant='span' affects='small'>
                {activeOrganization.organization.name}
              </Typography>
            </Typography>
          </div>
        </div>
      ) : (
        <CreateOrganizationForm />
      )}
    </StepperPanel>
  );
};

const OnboardCreateProject = () => {
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  return (
    <StepperPanel
      title='Create a new project'
      description='Create a new project to get started with Lilypad.'
    >
      {projects ? (
        <div className='p-6 rounded-lg border text-center'>
          <div className='flex flex-col items-center space-y-3'>
            <div className='text-blue-700 bg-blue-100 p-3 rounded-full'>
              <CircleCheck className='h-6 w-6' />
            </div>
            <h3 className='font-medium text-gray-900'>Project Created</h3>
            <Typography variant='p' affects='muted'>
              <Typography variant='span' affects='small'>
                {projects?.[0].name}
              </Typography>
            </Typography>
          </div>
        </div>
      ) : (
        <CreateProjectForm />
      )}
    </StepperPanel>
  );
};

const OnboardCreateEnvironment = () => {
  const { data: environments } = useSuspenseQuery(environmentsQueryOptions());
  return (
    <StepperPanel
      title='Create an environment'
      description='Create an environment for your project.'
    >
      {environments ? (
        <div className='p-6 rounded-lg border text-center'>
          <div className='flex flex-col items-center space-y-3'>
            <div className='text-blue-700 bg-blue-100 p-3 rounded-full'>
              <CircleCheck className='h-6 w-6' />
            </div>
            <h3 className='font-medium text-gray-900'>Environment Created</h3>
            <Typography variant='p' affects='muted'>
              <Typography variant='span' affects='small'>
                {environments?.[0].name}
              </Typography>
            </Typography>
          </div>
        </div>
      ) : (
        <CreateEnvironmentForm />
      )}
    </StepperPanel>
  );
};

interface OnboardCreateAPIKeyProps {
  apiKey: string | null;
  projectUuid: string | null;
  setApiKey: Dispatch<SetStateAction<string | null>>;
  setProjectUuid: Dispatch<SetStateAction<string | null>>;
}

const OnboardCreateAPIKey = ({
  apiKey,
  projectUuid,
  setApiKey,
  setProjectUuid,
}: OnboardCreateAPIKeyProps) => {
  return (
    <StepperPanel
      title='Create an API Key'
      description='Create an API key for your project.'
    >
      {!apiKey || !projectUuid ? (
        <CreateAPIKeyForm
          setApiKey={setApiKey}
          setProjectUuid={setProjectUuid}
        />
      ) : (
        <CopyKeyContent apiKey={apiKey} projectUuid={projectUuid} />
      )}
    </StepperPanel>
  );
};

interface OnboardRunFunctionProps {
  apiKey?: string | null;
  projectUuid?: string | null;
}

const OnboardRunFunction = ({
  apiKey,
  projectUuid,
}: OnboardRunFunctionProps) => {
  return (
    <StepperPanel
      title='Run a function'
      description='Now run a function and observe the results. You can use the API key and Project ID you just created to authenticate your requests.'
    >
      <>
        <Typography variant={"span"} affects='small' className='block mb-2'>
          Copy the code below or run your own function
        </Typography>
        <CodeSnippet
          className='w-full'
          code={`import os
import lilypad
from openai import OpenAI

os.environ["LILYPAD_API_KEY"] = "${apiKey ?? "YOUR_API_KEY"}"
os.environ["LILYPAD_PROJECT_ID"] = "${projectUuid ?? "YOUR_PROJECT_ID"}"

lilypad.configure()
client = OpenAI()

@lilypad.trace(versioning="automatic")
def answer_question(question: str) -> str | None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Answer this question: {question}"}],
    )
    return response.choices[0].message.content
    
response = answer_question("What is the capital of France?")
print(response)`}
        />
      </>
    </StepperPanel>
  );
};
