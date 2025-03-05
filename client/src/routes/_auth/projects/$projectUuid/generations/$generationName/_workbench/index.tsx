import { Playground } from '@/components/Playground'
import { Typography } from '@/components/ui/typography'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/_auth/projects/$projectUuid/generations/$generationName/_workbench/',
)({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <div className="p-4 flex flex-col gap-4">
      <Typography variant="h4">Create New Generation</Typography>
      <Playground version={null} />
    </div>
  )
}
