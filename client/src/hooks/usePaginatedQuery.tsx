import { useInfiniteQuery, InfiniteData } from '@tanstack/react-query'
import {
  fetchSpansByFunctionUuidPaged,
  type PageParam,
} from '@/utils/spans'
import { PAGE_SIZE } from '@/utils/constants'
import { type PaginatedSpanPublic } from '@/types/types'

export const usePaginatedSpansByFunction = (
  projectUuid: string,
  functionUuid?: string,
  { enabled = true }: { enabled?: boolean } = {},
) => {
  const isEnabled = enabled && !!functionUuid
  
  const queryKey = [
    'projects',
    projectUuid,
    'functions',
    functionUuid ?? 'disabled',
    'spans',
  ] as const
  
  return useInfiniteQuery<
    PaginatedSpanPublic,
    Error,
    InfiniteData<PaginatedSpanPublic, PageParam>,
    typeof queryKey,
    PageParam
  >({
    queryKey,
    enabled: isEnabled,
    initialPageParam: { offset: 0, limit: PAGE_SIZE },
    
    queryFn: ({ pageParam = { offset: 0, limit: PAGE_SIZE } }) => {
      if (!isEnabled) {
        return Promise.resolve({
          items: [],
          limit: PAGE_SIZE,
          offset: pageParam.offset,
          total: 0,
        })
      }
      
      return fetchSpansByFunctionUuidPaged(
        projectUuid,
        functionUuid,
        pageParam,
      ).then(page => ({
        ...page,
        items: page.items ?? [],
      }))
    },
    
    getNextPageParam: lastPage => {
      if (!isEnabled) return undefined
      
      const fetched = Array.isArray(lastPage.items) ? lastPage.items.length : 0
      const nextOffset = lastPage.offset + fetched
      
      return nextOffset >= lastPage.total
        ? undefined
        : ({ offset: nextOffset, limit: lastPage.limit } as PageParam)
    },
    
    
    staleTime: 30_000,
  })
}
