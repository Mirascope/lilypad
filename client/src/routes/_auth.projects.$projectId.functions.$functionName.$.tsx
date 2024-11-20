import { LLMFunction } from '@/components/LLMFunction'
import { NotFound } from '@/components/NotFound'
import { SelectVersionForm } from '@/components/SelectVerisonForm'
import { versionQueryOptions } from '@/utils/versions'
import { useSuspenseQuery } from '@tanstack/react-query'
import { createFileRoute, useParams } from '@tanstack/react-router'
export const Route = createFileRoute(
  '/_auth/projects/$projectId/functions/$functionName/$',
)({
  component: () => {
    const params = useParams({
      from: Route.id,
    })
    const { projectId: strProjectId, _splat } = params
    const strVersionId = _splat?.split('/')[1]
    if (!strProjectId) return <NotFound />
    const projectId = Number(strProjectId)
    const versionId = strVersionId ? Number(strVersionId) : undefined
    const { data: version } = useSuspenseQuery(
      versionQueryOptions(Number(projectId), Number(versionId)),
    )
    return (
      <div className="w-full">
        <SelectVersionForm versionId={versionId} />
        <LLMFunction projectId={Number(projectId)} version={version} />
      </div>
    )
  },
})
