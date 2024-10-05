/* prettier-ignore-start */

/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file is auto-generated by TanStack Router

import { createFileRoute } from '@tanstack/react-router'

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as LlmFunctionsLlmFunctionIdProviderCallParamsImport } from './routes/llmFunctions_.$llmFunctionId.providerCallParams'

// Create Virtual Routes

const TracesLazyImport = createFileRoute('/traces')()
const EditorLazyImport = createFileRoute('/editor')()
const DiffLazyImport = createFileRoute('/diff')()
const IndexLazyImport = createFileRoute('/')()

// Create/Update Routes

const TracesLazyRoute = TracesLazyImport.update({
  path: '/traces',
  getParentRoute: () => rootRoute,
} as any).lazy(() => import('./routes/traces.lazy').then((d) => d.Route))

const EditorLazyRoute = EditorLazyImport.update({
  path: '/editor',
  getParentRoute: () => rootRoute,
} as any).lazy(() => import('./routes/editor.lazy').then((d) => d.Route))

const DiffLazyRoute = DiffLazyImport.update({
  path: '/diff',
  getParentRoute: () => rootRoute,
} as any).lazy(() => import('./routes/diff.lazy').then((d) => d.Route))

const IndexLazyRoute = IndexLazyImport.update({
  path: '/',
  getParentRoute: () => rootRoute,
} as any).lazy(() => import('./routes/index.lazy').then((d) => d.Route))

const LlmFunctionsLlmFunctionIdProviderCallParamsRoute =
  LlmFunctionsLlmFunctionIdProviderCallParamsImport.update({
    path: '/llmFunctions/$llmFunctionId/providerCallParams',
    getParentRoute: () => rootRoute,
  } as any)

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/': {
      id: '/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof IndexLazyImport
      parentRoute: typeof rootRoute
    }
    '/diff': {
      id: '/diff'
      path: '/diff'
      fullPath: '/diff'
      preLoaderRoute: typeof DiffLazyImport
      parentRoute: typeof rootRoute
    }
    '/editor': {
      id: '/editor'
      path: '/editor'
      fullPath: '/editor'
      preLoaderRoute: typeof EditorLazyImport
      parentRoute: typeof rootRoute
    }
    '/traces': {
      id: '/traces'
      path: '/traces'
      fullPath: '/traces'
      preLoaderRoute: typeof TracesLazyImport
      parentRoute: typeof rootRoute
    }
    '/llmFunctions/$llmFunctionId/providerCallParams': {
      id: '/llmFunctions/$llmFunctionId/providerCallParams'
      path: '/llmFunctions/$llmFunctionId/providerCallParams'
      fullPath: '/llmFunctions/$llmFunctionId/providerCallParams'
      preLoaderRoute: typeof LlmFunctionsLlmFunctionIdProviderCallParamsImport
      parentRoute: typeof rootRoute
    }
  }
}

// Create and export the route tree

export interface FileRoutesByFullPath {
  '/': typeof IndexLazyRoute
  '/diff': typeof DiffLazyRoute
  '/editor': typeof EditorLazyRoute
  '/traces': typeof TracesLazyRoute
  '/llmFunctions/$llmFunctionId/providerCallParams': typeof LlmFunctionsLlmFunctionIdProviderCallParamsRoute
}

export interface FileRoutesByTo {
  '/': typeof IndexLazyRoute
  '/diff': typeof DiffLazyRoute
  '/editor': typeof EditorLazyRoute
  '/traces': typeof TracesLazyRoute
  '/llmFunctions/$llmFunctionId/providerCallParams': typeof LlmFunctionsLlmFunctionIdProviderCallParamsRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/': typeof IndexLazyRoute
  '/diff': typeof DiffLazyRoute
  '/editor': typeof EditorLazyRoute
  '/traces': typeof TracesLazyRoute
  '/llmFunctions/$llmFunctionId/providerCallParams': typeof LlmFunctionsLlmFunctionIdProviderCallParamsRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths:
    | '/'
    | '/diff'
    | '/editor'
    | '/traces'
    | '/llmFunctions/$llmFunctionId/providerCallParams'
  fileRoutesByTo: FileRoutesByTo
  to:
    | '/'
    | '/diff'
    | '/editor'
    | '/traces'
    | '/llmFunctions/$llmFunctionId/providerCallParams'
  id:
    | '__root__'
    | '/'
    | '/diff'
    | '/editor'
    | '/traces'
    | '/llmFunctions/$llmFunctionId/providerCallParams'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  IndexLazyRoute: typeof IndexLazyRoute
  DiffLazyRoute: typeof DiffLazyRoute
  EditorLazyRoute: typeof EditorLazyRoute
  TracesLazyRoute: typeof TracesLazyRoute
  LlmFunctionsLlmFunctionIdProviderCallParamsRoute: typeof LlmFunctionsLlmFunctionIdProviderCallParamsRoute
}

const rootRouteChildren: RootRouteChildren = {
  IndexLazyRoute: IndexLazyRoute,
  DiffLazyRoute: DiffLazyRoute,
  EditorLazyRoute: EditorLazyRoute,
  TracesLazyRoute: TracesLazyRoute,
  LlmFunctionsLlmFunctionIdProviderCallParamsRoute:
    LlmFunctionsLlmFunctionIdProviderCallParamsRoute,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* prettier-ignore-end */

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/",
        "/diff",
        "/editor",
        "/traces",
        "/llmFunctions/$llmFunctionId/providerCallParams"
      ]
    },
    "/": {
      "filePath": "index.lazy.tsx"
    },
    "/diff": {
      "filePath": "diff.lazy.tsx"
    },
    "/editor": {
      "filePath": "editor.lazy.tsx"
    },
    "/traces": {
      "filePath": "traces.lazy.tsx"
    },
    "/llmFunctions/$llmFunctionId/providerCallParams": {
      "filePath": "llmFunctions_.$llmFunctionId.providerCallParams.tsx"
    }
  }
}
ROUTE_MANIFEST_END */
