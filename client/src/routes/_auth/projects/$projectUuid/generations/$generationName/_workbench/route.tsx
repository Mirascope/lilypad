import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  generationsByNameQueryOptions,
  useArchiveGenerationMutation,
} from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  Outlet,
  useNavigate,
  useParams,
} from "@tanstack/react-router";

import LilypadDialog from "@/components/LilypadDialog";
import { LilypadLoading } from "@/components/LilypadLoading";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Typography } from "@/components/ui/typography";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { GenerationTab } from "@/types/generations";
import { GitCompare, Plus, Trash } from "lucide-react";
import { JSX, Suspense, useState } from "react";

type GenerationRouteParams = {
  projectUuid: string;
  generationName: string;
  generationUuid: string;
  secondGenerationUuid?: string;
  isCompare: boolean;
  tab: GenerationTab;
};
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/_workbench"
)({
  params: {
    stringify(params: GenerationRouteParams) {
      return {
        projectUuid: params.projectUuid,
        generationName: params.generationName,
      };
    },
    parse(raw: Record<string, string>): GenerationRouteParams {
      let tab = raw.tab;
      if (!Object.values(GenerationTab).includes(tab as GenerationTab)) {
        tab = GenerationTab.OVERVIEW;
      }
      return {
        projectUuid: raw.projectUuid,
        generationName: raw.generationName,
        generationUuid: raw.generationUuid || raw.firstGenerationUuid,
        secondGenerationUuid: raw.secondGenerationUuid,
        tab: tab as GenerationTab,
        isCompare: Boolean(raw.firstGenerationUuid),
      };
    },
  },
  validateSearch: (search): search is { tab: GenerationTab } => {
    const tab = search.tab;
    return Object.values(GenerationTab).includes(tab as GenerationTab);
  },

  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <GenerationWorkbench />
    </Suspense>
  ),
});

type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
  isAvailable: boolean;
};

const GenerationWorkbench = () => {
  const {
    projectUuid,
    generationName,
    generationUuid,
    secondGenerationUuid,
    tab,
    isCompare,
  } = useParams({
    from: Route.id,
  });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );
  const [compareMode, setCompareMode] = useState<boolean>(isCompare);
  const features = useFeatureAccess();
  const navigate = useNavigate();
  const generation = generations.find(
    (generation) => generation.uuid === generationUuid
  );
  const archiveGeneration = useArchiveGenerationMutation();
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: GenerationTab.OVERVIEW,
      isAvailable: features.generations,
    },
    {
      label: "Traces",
      value: GenerationTab.TRACES,
      isAvailable: features.traces,
    },
    {
      label: "Annotations",
      value: GenerationTab.ANNOTATIONS,
      isAvailable: features.annotations,
    },
  ];
  const handleArchive = async () => {
    if (!generation) return;
    await archiveGeneration.mutateAsync({
      projectUuid,
      generationUuid: generation.uuid,
      generationName,
    });
    navigate({ to: `/projects/${projectUuid}/generations` });
  };

  const handleNewGenerationClick = () => {
    navigate({
      to: `/projects/${projectUuid}/generations/${generationName}`,
    });
  };

  const handleTabChange = (newTab: string) => {
    if (compareMode) {
      navigate({
        to: `/projects/${projectUuid}/generations/${generationName}/compare/$firstGenerationUuid/$secondGenerationUuid/$tab`,
        params: {
          firstGenerationUuid: generationUuid,
          secondGenerationUuid,
          tab: newTab as GenerationTab,
        },
      });
    } else {
      navigate({
        to: `/projects/${projectUuid}/generations/${generationName}/${generationUuid}/${newTab}`,
      });
    }
  };

  const tabWidth = 80 * tabs.length;
  return (
    <div className='w-full p-6 flex flex-col gap-1'>
      <div className='flex gap-2'>
        <Typography variant='h2'>{generationName}</Typography>
        {features.managedGenerations && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size='icon' onClick={handleNewGenerationClick}>
                <Plus />
              </Button>
            </TooltipTrigger>
            <TooltipContent className='bg-gray-700 text-white'>
              Create a new managed generation
            </TooltipContent>
          </Tooltip>
        )}
      </div>
      <div className='flex gap-2 items-center'>
        {generation && (
          <Button
            variant='outline'
            size='icon'
            onClick={() => {
              if (!compareMode) {
                navigate({
                  to: `/projects/${projectUuid}/generations/${generationName}/compare/$firstGenerationUuid/$secondGenerationUuid/$tab`,
                  params: {
                    firstGenerationUuid: generationUuid,
                    secondGenerationUuid,
                    tab,
                  },
                });
              } else {
                navigate({
                  to: `/projects/${projectUuid}/generations/${generationName}/${generationUuid}/${tab}`,
                });
              }
              setCompareMode((prevCompareMode) => !prevCompareMode);
            }}
          >
            <GitCompare />
          </Button>
        )}
        <SelectGeneration compareMode={compareMode} isFirstGeneration={true} />
        {generation && !isCompare && (
          <LilypadDialog
            icon={<Trash />}
            title={`Delete ${generation.name} v${generation.version_num}`}
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
                type='button'
                variant='destructive'
                onClick={handleArchive}
              >
                Delete
              </Button>,
              <Button type='button' variant='outline'>
                Cancel
              </Button>,
            ]}
          >
            {`Are you sure you want to delete ${generation.name} v${generation.version_num}?`}
          </LilypadDialog>
        )}
      </div>
      {compareMode && (
        <div className='flex gap-2 items-center'>
          <div className='w-10 h-10'></div>
          <SelectGeneration
            compareMode={compareMode}
            isFirstGeneration={false}
          />
        </div>
      )}
      <Tabs value={tab} onValueChange={handleTabChange} className='w-full'>
        <div className='flex justify-center w-full'>
          <TabsList className={`w-[${tabWidth}px]`}>
            {tabs.map((tab) => {
              return (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  disabled={!tab.isAvailable}
                >
                  {tab.label}
                </TabsTrigger>
              );
            })}
          </TabsList>
        </div>
        <Separator className='my-2' />
        <Suspense fallback={<LilypadLoading />}>
          {tabs.map((tab) => (
            <TabsContent key={tab.value} value={tab.value} className='w-full'>
              <Outlet />
            </TabsContent>
          ))}
        </Suspense>
      </Tabs>
    </div>
  );
};

const SelectGeneration = ({
  compareMode,
  isFirstGeneration,
}: {
  compareMode?: boolean;
  isFirstGeneration?: boolean;
}) => {
  const {
    projectUuid,
    generationName,
    generationUuid: firstGenerationUuid,
    secondGenerationUuid,
    tab,
  } = useParams({
    from: Route.id,
  });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );
  const navigate = useNavigate();
  return (
    <Select
      value={
        (isFirstGeneration ? firstGenerationUuid : secondGenerationUuid) || ""
      }
      onValueChange={(uuid) => {
        if (compareMode) {
          navigate({
            to: `/projects/${projectUuid}/generations/${generationName}/compare/$firstGenerationUuid/$secondGenerationUuid/$tab`,
            params: {
              firstGenerationUuid: isFirstGeneration
                ? uuid
                : firstGenerationUuid,
              secondGenerationUuid: isFirstGeneration
                ? secondGenerationUuid
                : uuid,
              tab,
            },
          });
        } else {
          navigate({
            to: `/projects/${projectUuid}/generations/${generationName}/${uuid}/${tab}`,
          });
        }
      }}
    >
      <SelectTrigger className='w-[200px]'>
        <SelectValue placeholder='Select a generation' />
      </SelectTrigger>
      <SelectContent>
        {generations.map((generation) => (
          <SelectItem
            key={generation.uuid}
            value={generation.uuid}
            disabled={
              (!isFirstGeneration && generation.uuid === firstGenerationUuid) ||
              (isFirstGeneration && generation.uuid === secondGenerationUuid)
            }
          >
            v{generation.version_num}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
