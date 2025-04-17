import LilypadDialog from "@/components/LilypadDialog";
import { LilypadLoading } from "@/components/LilypadLoading";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Typography } from "@/components/ui/typography";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { useToast } from "@/hooks/use-toast";
import { FunctionTab } from "@/types/functions";
import {
  functionsByNameQueryOptions,
  useArchiveFunctionMutation,
} from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  Outlet,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { GitCompare, Trash } from "lucide-react";
import { JSX, Suspense, useState } from "react";
import { validate } from "uuid";

export interface FunctionRouteParams {
  projectUuid: string;
  functionName: string;
  functionUuid: string;
  secondFunctionUuid?: string;
  isCompare: boolean;
  tab: FunctionTab;
  _splat?: string;
}
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/functions/$functionName/_workbench"
)({
  params: {
    stringify(params: FunctionRouteParams) {
      return {
        projectUuid: params.projectUuid,
        functionName: params.functionName,
      };
    },
    parse(raw: Record<string, string>): FunctionRouteParams {
      let tab = raw.tab;
      if (!Object.values(FunctionTab).includes(tab as FunctionTab)) {
        tab = FunctionTab.OVERVIEW;
      }
      return {
        projectUuid: raw.projectUuid,
        functionName: raw.functionName,
        functionUuid: raw.functionUuid || raw.firstFunctionUuid,
        secondFunctionUuid: validate(raw.secondFunctionUuid)
          ? raw.secondFunctionUuid
          : undefined,
        tab: tab as FunctionTab,
        isCompare: Boolean(raw.firstFunctionUuid),
      };
    },
  },
  validateSearch: (search): search is { tab: FunctionTab } => {
    const tab = search.tab;
    return Object.values(FunctionTab).includes(tab as FunctionTab);
  },

  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <FunctionWorkbench />
    </Suspense>
  ),
});

interface Tab {
  label: string;
  value: string;
  component?: JSX.Element | null;
  isAvailable: boolean;
}

const FunctionWorkbench = () => {
  const {
    projectUuid,
    functionName,
    functionUuid,
    secondFunctionUuid,
    tab,
    isCompare,
  } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const { toast } = useToast();
  const [compareMode, setCompareMode] = useState<boolean>(isCompare);
  const features = useFeatureAccess();
  const navigate = useNavigate();
  const fn = functions.find((f) => f.uuid === functionUuid);
  const archiveFunction = useArchiveFunctionMutation();
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: FunctionTab.OVERVIEW,
      isAvailable: features.functions,
    },
    {
      label: "Traces",
      value: FunctionTab.TRACES,
      isAvailable: features.traces,
    },
    {
      label: "Annotations",
      value: FunctionTab.ANNOTATIONS,
      isAvailable: features.annotations,
    },
  ];
  const handleArchive = async () => {
    if (!fn) return;
    await archiveFunction.mutateAsync({
      projectUuid,
      functionUuid: fn.uuid,
      functionName,
    });
    navigate({ to: `/projects/${projectUuid}/functions` }).catch(() =>
      toast({
        title: "Failed to navigate",
      })
    );
  };

  const handleTabChange = (newTab: string) => {
    if (compareMode) {
      navigate({
        to: `/projects/${projectUuid}/functions/${functionName}/compare/$firstFunctionUuid/$secondFunctionUuid/$tab`,
        params: {
          firstFunctionUuid: functionUuid,
          secondFunctionUuid,
          tab: newTab as FunctionTab,
        },
      }).catch(() =>
        toast({
          title: "Failed to navigate",
        })
      );
    } else {
      navigate({
        to: `/projects/${projectUuid}/functions/${functionName}/${functionUuid}/${newTab}`,
      }).catch(() =>
        toast({
          title: "Failed to navigate",
        })
      );
    }
  };

  const tabWidth = 80 * tabs.length;
  return (
    <div className='pt-4 pb-1 h-screen flex flex-col px-2'>
      <Typography variant='h2'>{functionName}</Typography>
      <div className='flex gap-2 items-center'>
        {fn && (
          <Button
            variant='outline'
            size='icon'
            onClick={() => {
              if (!compareMode) {
                navigate({
                  to: `/projects/${projectUuid}/functions/${functionName}/compare/$firstFunctionUuid/$secondFunctionUuid/$tab`,
                  params: {
                    firstFunctionUuid: functionUuid,
                    secondFunctionUuid,
                    tab,
                  },
                }).catch(() =>
                  toast({
                    title: "Failed to navigate",
                  })
                );
              } else {
                navigate({
                  to: `/projects/${projectUuid}/functions/${functionName}/${functionUuid}/${tab}`,
                }).catch(() =>
                  toast({
                    title: "Failed to navigate",
                  })
                );
              }
              setCompareMode((prevCompareMode) => !prevCompareMode);
            }}
          >
            <GitCompare />
          </Button>
        )}
        <SelectFunction compareMode={compareMode} isFirstFunction={true} />
        {fn && !isCompare && (
          <LilypadDialog
            icon={<Trash />}
            title={`Delete ${fn.name} v${fn.version_num}`}
            description=''
            dialogContentProps={{
              className: "max-w-[600px]",
            }}
            buttonProps={{
              variant: "outlineDestructive",
              className: "w-9 h-9",
            }}
            dialogButtons={[
              <Button
                key='delete-function'
                type='button'
                variant='destructive'
                onClick={handleArchive}
              >
                Delete
              </Button>,
              <Button
                key='cancel-delete-button'
                type='button'
                variant='outline'
              >
                Cancel
              </Button>,
            ]}
          >
            {`Are you sure you want to delete ${fn.name} v${fn.version_num}?`}
          </LilypadDialog>
        )}
      </div>
      {compareMode && (
        <div className='flex gap-2 items-center'>
          <div className='w-10 h-10'></div>
          <SelectFunction compareMode={compareMode} isFirstFunction={false} />
        </div>
      )}
      <Tabs
        value={tab}
        onValueChange={handleTabChange}
        className='w-full h-full flex flex-col'
      >
        <div>
          <div className='flex justify-center w-full'>
            <TabsList className={`w-[${tabWidth}px]`}>
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  disabled={!tab.isAvailable}
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
              className='absolute inset-0 overflow-auto'
            >
              <Outlet />
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </div>
  );
};

const SelectFunction = ({
  compareMode,
  isFirstFunction,
}: {
  compareMode?: boolean;
  isFirstFunction?: boolean;
}) => {
  const {
    projectUuid,
    functionName,
    functionUuid: firstFunctionUuid,
    secondFunctionUuid,
    tab,
  } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const { toast } = useToast();
  const navigate = useNavigate();
  return (
    <Select
      value={(isFirstFunction ? firstFunctionUuid : secondFunctionUuid) ?? ""}
      onValueChange={(uuid) => {
        if (compareMode) {
          navigate({
            to: `/projects/${projectUuid}/functions/${functionName}/compare/$firstFunctionUuid/$secondFunctionUuid/$tab`,
            params: {
              firstFunctionUuid: isFirstFunction ? uuid : firstFunctionUuid,
              secondFunctionUuid: isFirstFunction ? secondFunctionUuid : uuid,
              tab,
            },
          }).catch(() =>
            toast({
              title: "Failed to navigate",
            })
          );
        } else {
          navigate({
            to: `/projects/${projectUuid}/functions/${functionName}/${uuid}/${tab}`,
          }).catch(() =>
            toast({
              title: "Failed to navigate",
            })
          );
        }
      }}
    >
      <SelectTrigger className='w-[200px]'>
        <SelectValue placeholder='Select a function' />
      </SelectTrigger>
      <SelectContent>
        {functions.map((fn) => (
          <SelectItem
            key={fn.uuid}
            value={fn.uuid}
            disabled={
              (!isFirstFunction && fn.uuid === firstFunctionUuid) ||
              (isFirstFunction && fn.uuid === secondFunctionUuid)
            }
          >
            v{fn.version_num}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
