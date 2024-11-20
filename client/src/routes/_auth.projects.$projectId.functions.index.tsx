import {
  createFileRoute,
  Link,
  useNavigate,
  useParams,
} from '@tanstack/react-router'
import { Input } from '@/components/ui/input'
import { Typography } from '@/components/ui/typography'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { uniqueFunctionNamesQueryOptions } from '@/utils/functions'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
export const Route = createFileRoute('/_auth/projects/$projectId/functions/')({
  component: () => <CreatePrompt />,
})

export const CreatePrompt = () => {
  const { projectId } = useParams({ from: Route.id })
  const { data: functionNames } = useSuspenseQuery(
    uniqueFunctionNamesQueryOptions(Number(projectId)),
  )
  const [value, setValue] = useState('')
  const navigate = useNavigate()
  const handleClick = (e) => {
    e.preventDefault()
    navigate({
      to: `/projects/${projectId}/functions/${value}`,
    })
  }
  return (
    <div className="min-h-screen flex flex-col items-center w-[600px] m-auto">
      <Typography variant="h3">Functions</Typography>
      <div className="flex flex-wrap gap-2">
        {functionNames.length > 0 &&
          functionNames.map((functionName) => (
            <Link
              key={functionName}
              to={`/projects/${projectId}/functions/${functionName}`}
            >
              <Card className="flex items-center justify-center transition-colors hover:bg-gray-100 dark:hover:bg-gray-800">
                <CardContent className="p-4">{functionName}</CardContent>
              </Card>
            </Link>
          ))}
      </div>
      <Separator className="my-4" />
      <form className=" flex flex-col gap-2">
        <Typography variant="h3">Create a new function</Typography>
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Enter function name"
        />
        <Button onClick={handleClick}>Get Started</Button>
      </form>
    </div>
  )
}
