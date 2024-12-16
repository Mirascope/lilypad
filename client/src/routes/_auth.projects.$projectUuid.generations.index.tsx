import { generationsQueryOptions } from "@/utils/generations";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { GenerationPublic } from "@/types/types";
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/"
)({
  component: () => <GenerationsList />,
});

const GenerationCards = ({
  generation,
  index,
}: {
  generation: GenerationPublic;
  index: number;
}) => {
  const navigate = useNavigate();
  const { projectUuid } = useParams({ from: Route.id });
  const handleClick = () => {
    navigate({ to: `/projects/${projectUuid}/generations/${generation.uuid}` });
  };
  return (
    <Card className='w-auto' onClick={handleClick}>
      <CardHeader>
        <CardTitle>{generation.name}</CardTitle>
        <CardDescription>Version {index + 1}</CardDescription>
      </CardHeader>
      <CardContent className='flex gap-2'></CardContent>
    </Card>
  );
};
const GenerationsList = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data } = useSuspenseQuery(generationsQueryOptions(projectUuid));
  return (
    <div className='flex'>
      {data.map((generation, i) => (
        <GenerationCards
          key={generation.uuid}
          generation={generation}
          index={i}
        />
      ))}
    </div>
  );
};
