/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

import { createFileRoute } from '@tanstack/react-router'

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as AuthImport } from './routes/_auth'
import { Route as IndexImport } from './routes/index'
import { Route as JoinTokenImport } from './routes/join.$token'
import { Route as AuthLoginImport } from './routes/auth.login'
import { Route as AuthCallbackImport } from './routes/auth.callback'
import { Route as AuthProjectsIndexImport } from './routes/_auth/projects/index'
import { Route as AuthSettingsSplatImport } from './routes/_auth/settings.$'
import { Route as AuthProjectsProjectUuidIndexImport } from './routes/_auth/projects/$projectUuid.index'
import { Route as AuthProjectsProjectsProjectUuidImport } from './routes/_auth/projects/projects.$projectUuid'
import { Route as AuthProjectsProjectUuidPlaygroundRouteImport } from './routes/_auth/projects/$projectUuid/playground/route'
import { Route as AuthProjectsProjectUuidFunctionsIndexImport } from './routes/_auth/projects/$projectUuid/functions/index'
import { Route as AuthProjectsProjectUuidAnnotationsIndexImport } from './routes/_auth/projects/$projectUuid/annotations/index'
import { Route as AuthProjectsProjectUuidTracesSplatImport } from './routes/_auth/projects/$projectUuid/traces.$'
import { Route as AuthProjectsProjectUuidPlaygroundFunctionNameLayoutImport } from './routes/_auth/projects/$projectUuid/playground/$functionName/_layout'
import { Route as AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteImport } from './routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/route'
import { Route as AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexImport } from './routes/_auth/projects/$projectUuid/playground/$functionName/_layout/index'
import { Route as AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexImport } from './routes/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid.index'
import { Route as AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidImport } from './routes/_auth/projects/$projectUuid/playground/$functionName/compare.$firstFunctionUuid.$secondFunctionUuid'
import { Route as AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabImport } from './routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab'
import { Route as AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabImport } from './routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare.$firstFunctionUuid.$secondFunctionUuid.$tab'

// Create Virtual Routes

const AuthProjectsProjectUuidPlaygroundFunctionNameImport = createFileRoute(
  '/_auth/projects/$projectUuid/playground/$functionName',
)()
const AuthProjectsProjectUuidFunctionsFunctionNameImport = createFileRoute(
  '/_auth/projects/$projectUuid/functions/$functionName',
)()

// Create/Update Routes

const AuthRoute = AuthImport.update({
  id: '/_auth',
  getParentRoute: () => rootRoute,
} as any)

const IndexRoute = IndexImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => rootRoute,
} as any)

const JoinTokenRoute = JoinTokenImport.update({
  id: '/join/$token',
  path: '/join/$token',
  getParentRoute: () => rootRoute,
} as any)

const AuthLoginRoute = AuthLoginImport.update({
  id: '/auth/login',
  path: '/auth/login',
  getParentRoute: () => rootRoute,
} as any)

const AuthCallbackRoute = AuthCallbackImport.update({
  id: '/auth/callback',
  path: '/auth/callback',
  getParentRoute: () => rootRoute,
} as any)

const AuthProjectsIndexRoute = AuthProjectsIndexImport.update({
  id: '/projects/',
  path: '/projects/',
  getParentRoute: () => AuthRoute,
} as any)

const AuthSettingsSplatRoute = AuthSettingsSplatImport.update({
  id: '/settings/$',
  path: '/settings/$',
  getParentRoute: () => AuthRoute,
} as any)

const AuthProjectsProjectUuidIndexRoute =
  AuthProjectsProjectUuidIndexImport.update({
    id: '/projects/$projectUuid/',
    path: '/projects/$projectUuid/',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectsProjectUuidRoute =
  AuthProjectsProjectsProjectUuidImport.update({
    id: '/projects/projects/$projectUuid',
    path: '/projects/projects/$projectUuid',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectUuidPlaygroundRouteRoute =
  AuthProjectsProjectUuidPlaygroundRouteImport.update({
    id: '/projects/$projectUuid/playground',
    path: '/projects/$projectUuid/playground',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectUuidPlaygroundFunctionNameRoute =
  AuthProjectsProjectUuidPlaygroundFunctionNameImport.update({
    id: '/$functionName',
    path: '/$functionName',
    getParentRoute: () => AuthProjectsProjectUuidPlaygroundRouteRoute,
  } as any)

const AuthProjectsProjectUuidFunctionsFunctionNameRoute =
  AuthProjectsProjectUuidFunctionsFunctionNameImport.update({
    id: '/projects/$projectUuid/functions/$functionName',
    path: '/projects/$projectUuid/functions/$functionName',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectUuidFunctionsIndexRoute =
  AuthProjectsProjectUuidFunctionsIndexImport.update({
    id: '/projects/$projectUuid/functions/',
    path: '/projects/$projectUuid/functions/',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectUuidAnnotationsIndexRoute =
  AuthProjectsProjectUuidAnnotationsIndexImport.update({
    id: '/projects/$projectUuid/annotations/',
    path: '/projects/$projectUuid/annotations/',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectUuidTracesSplatRoute =
  AuthProjectsProjectUuidTracesSplatImport.update({
    id: '/projects/$projectUuid/traces/$',
    path: '/projects/$projectUuid/traces/$',
    getParentRoute: () => AuthRoute,
  } as any)

const AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRoute =
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutImport.update({
    id: '/_layout',
    getParentRoute: () => AuthProjectsProjectUuidPlaygroundFunctionNameRoute,
  } as any)

const AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRoute =
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteImport.update({
    id: '/_workbench',
    getParentRoute: () => AuthProjectsProjectUuidFunctionsFunctionNameRoute,
  } as any)

const AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute =
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexImport.update({
    id: '/',
    path: '/',
    getParentRoute: () =>
      AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRoute,
  } as any)

const AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute =
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexImport.update(
    {
      id: '/$functionUuid/',
      path: '/$functionUuid/',
      getParentRoute: () =>
        AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRoute,
    } as any,
  )

const AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute =
  AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidImport.update(
    {
      id: '/compare/$firstFunctionUuid/$secondFunctionUuid',
      path: '/compare/$firstFunctionUuid/$secondFunctionUuid',
      getParentRoute: () => AuthProjectsProjectUuidPlaygroundFunctionNameRoute,
    } as any,
  )

const AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute =
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabImport.update(
    {
      id: '/$functionUuid/$tab',
      path: '/$functionUuid/$tab',
      getParentRoute: () =>
        AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRoute,
    } as any,
  )

const AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute =
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabImport.update(
    {
      id: '/compare/$firstFunctionUuid/$secondFunctionUuid/$tab',
      path: '/compare/$firstFunctionUuid/$secondFunctionUuid/$tab',
      getParentRoute: () =>
        AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRoute,
    } as any,
  )

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/': {
      id: '/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof IndexImport
      parentRoute: typeof rootRoute
    }
    '/_auth': {
      id: '/_auth'
      path: ''
      fullPath: ''
      preLoaderRoute: typeof AuthImport
      parentRoute: typeof rootRoute
    }
    '/auth/callback': {
      id: '/auth/callback'
      path: '/auth/callback'
      fullPath: '/auth/callback'
      preLoaderRoute: typeof AuthCallbackImport
      parentRoute: typeof rootRoute
    }
    '/auth/login': {
      id: '/auth/login'
      path: '/auth/login'
      fullPath: '/auth/login'
      preLoaderRoute: typeof AuthLoginImport
      parentRoute: typeof rootRoute
    }
    '/join/$token': {
      id: '/join/$token'
      path: '/join/$token'
      fullPath: '/join/$token'
      preLoaderRoute: typeof JoinTokenImport
      parentRoute: typeof rootRoute
    }
    '/_auth/settings/$': {
      id: '/_auth/settings/$'
      path: '/settings/$'
      fullPath: '/settings/$'
      preLoaderRoute: typeof AuthSettingsSplatImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/': {
      id: '/_auth/projects/'
      path: '/projects'
      fullPath: '/projects'
      preLoaderRoute: typeof AuthProjectsIndexImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/playground': {
      id: '/_auth/projects/$projectUuid/playground'
      path: '/projects/$projectUuid/playground'
      fullPath: '/projects/$projectUuid/playground'
      preLoaderRoute: typeof AuthProjectsProjectUuidPlaygroundRouteImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/projects/$projectUuid': {
      id: '/_auth/projects/projects/$projectUuid'
      path: '/projects/projects/$projectUuid'
      fullPath: '/projects/projects/$projectUuid'
      preLoaderRoute: typeof AuthProjectsProjectsProjectUuidImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/': {
      id: '/_auth/projects/$projectUuid/'
      path: '/projects/$projectUuid'
      fullPath: '/projects/$projectUuid'
      preLoaderRoute: typeof AuthProjectsProjectUuidIndexImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/traces/$': {
      id: '/_auth/projects/$projectUuid/traces/$'
      path: '/projects/$projectUuid/traces/$'
      fullPath: '/projects/$projectUuid/traces/$'
      preLoaderRoute: typeof AuthProjectsProjectUuidTracesSplatImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/annotations/': {
      id: '/_auth/projects/$projectUuid/annotations/'
      path: '/projects/$projectUuid/annotations'
      fullPath: '/projects/$projectUuid/annotations'
      preLoaderRoute: typeof AuthProjectsProjectUuidAnnotationsIndexImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/functions/': {
      id: '/_auth/projects/$projectUuid/functions/'
      path: '/projects/$projectUuid/functions'
      fullPath: '/projects/$projectUuid/functions'
      preLoaderRoute: typeof AuthProjectsProjectUuidFunctionsIndexImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/functions/$functionName': {
      id: '/_auth/projects/$projectUuid/functions/$functionName'
      path: '/projects/$projectUuid/functions/$functionName'
      fullPath: '/projects/$projectUuid/functions/$functionName'
      preLoaderRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameImport
      parentRoute: typeof AuthImport
    }
    '/_auth/projects/$projectUuid/functions/$functionName/_workbench': {
      id: '/_auth/projects/$projectUuid/functions/$functionName/_workbench'
      path: '/projects/$projectUuid/functions/$functionName'
      fullPath: '/projects/$projectUuid/functions/$functionName'
      preLoaderRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteImport
      parentRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameRoute
    }
    '/_auth/projects/$projectUuid/playground/$functionName': {
      id: '/_auth/projects/$projectUuid/playground/$functionName'
      path: '/$functionName'
      fullPath: '/projects/$projectUuid/playground/$functionName'
      preLoaderRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameImport
      parentRoute: typeof AuthProjectsProjectUuidPlaygroundRouteImport
    }
    '/_auth/projects/$projectUuid/playground/$functionName/_layout': {
      id: '/_auth/projects/$projectUuid/playground/$functionName/_layout'
      path: '/$functionName'
      fullPath: '/projects/$projectUuid/playground/$functionName'
      preLoaderRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutImport
      parentRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameRoute
    }
    '/_auth/projects/$projectUuid/playground/$functionName/_layout/': {
      id: '/_auth/projects/$projectUuid/playground/$functionName/_layout/'
      path: '/'
      fullPath: '/projects/$projectUuid/playground/$functionName/'
      preLoaderRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexImport
      parentRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutImport
    }
    '/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab': {
      id: '/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab'
      path: '/$functionUuid/$tab'
      fullPath: '/projects/$projectUuid/functions/$functionName/$functionUuid/$tab'
      preLoaderRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabImport
      parentRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteImport
    }
    '/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid': {
      id: '/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid'
      path: '/compare/$firstFunctionUuid/$secondFunctionUuid'
      fullPath: '/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid'
      preLoaderRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidImport
      parentRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameImport
    }
    '/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/': {
      id: '/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/'
      path: '/$functionUuid'
      fullPath: '/projects/$projectUuid/playground/$functionName/$functionUuid'
      preLoaderRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexImport
      parentRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutImport
    }
    '/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab': {
      id: '/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab'
      path: '/compare/$firstFunctionUuid/$secondFunctionUuid/$tab'
      fullPath: '/projects/$projectUuid/functions/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid/$tab'
      preLoaderRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabImport
      parentRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteImport
    }
  }
}

// Create and export the route tree

interface AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteChildren {
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute
}

const AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteChildren: AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteChildren =
  {
    AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute:
      AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute,
    AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute:
      AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute,
  }

const AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteWithChildren =
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRoute._addFileChildren(
    AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteChildren,
  )

interface AuthProjectsProjectUuidPlaygroundFunctionNameRouteChildren {
  AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteWithChildren
  AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute
}

const AuthProjectsProjectUuidPlaygroundFunctionNameRouteChildren: AuthProjectsProjectUuidPlaygroundFunctionNameRouteChildren =
  {
    AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRoute:
      AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteWithChildren,
    AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute:
      AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute,
  }

const AuthProjectsProjectUuidPlaygroundFunctionNameRouteWithChildren =
  AuthProjectsProjectUuidPlaygroundFunctionNameRoute._addFileChildren(
    AuthProjectsProjectUuidPlaygroundFunctionNameRouteChildren,
  )

interface AuthProjectsProjectUuidPlaygroundRouteRouteChildren {
  AuthProjectsProjectUuidPlaygroundFunctionNameRoute: typeof AuthProjectsProjectUuidPlaygroundFunctionNameRouteWithChildren
}

const AuthProjectsProjectUuidPlaygroundRouteRouteChildren: AuthProjectsProjectUuidPlaygroundRouteRouteChildren =
  {
    AuthProjectsProjectUuidPlaygroundFunctionNameRoute:
      AuthProjectsProjectUuidPlaygroundFunctionNameRouteWithChildren,
  }

const AuthProjectsProjectUuidPlaygroundRouteRouteWithChildren =
  AuthProjectsProjectUuidPlaygroundRouteRoute._addFileChildren(
    AuthProjectsProjectUuidPlaygroundRouteRouteChildren,
  )

interface AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteChildren {
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute
}

const AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteChildren: AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteChildren =
  {
    AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute:
      AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute,
    AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute:
      AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute,
  }

const AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteWithChildren =
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRoute._addFileChildren(
    AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteChildren,
  )

interface AuthProjectsProjectUuidFunctionsFunctionNameRouteChildren {
  AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteWithChildren
}

const AuthProjectsProjectUuidFunctionsFunctionNameRouteChildren: AuthProjectsProjectUuidFunctionsFunctionNameRouteChildren =
  {
    AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRoute:
      AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteWithChildren,
  }

const AuthProjectsProjectUuidFunctionsFunctionNameRouteWithChildren =
  AuthProjectsProjectUuidFunctionsFunctionNameRoute._addFileChildren(
    AuthProjectsProjectUuidFunctionsFunctionNameRouteChildren,
  )

interface AuthRouteChildren {
  AuthSettingsSplatRoute: typeof AuthSettingsSplatRoute
  AuthProjectsIndexRoute: typeof AuthProjectsIndexRoute
  AuthProjectsProjectUuidPlaygroundRouteRoute: typeof AuthProjectsProjectUuidPlaygroundRouteRouteWithChildren
  AuthProjectsProjectsProjectUuidRoute: typeof AuthProjectsProjectsProjectUuidRoute
  AuthProjectsProjectUuidIndexRoute: typeof AuthProjectsProjectUuidIndexRoute
  AuthProjectsProjectUuidTracesSplatRoute: typeof AuthProjectsProjectUuidTracesSplatRoute
  AuthProjectsProjectUuidAnnotationsIndexRoute: typeof AuthProjectsProjectUuidAnnotationsIndexRoute
  AuthProjectsProjectUuidFunctionsIndexRoute: typeof AuthProjectsProjectUuidFunctionsIndexRoute
  AuthProjectsProjectUuidFunctionsFunctionNameRoute: typeof AuthProjectsProjectUuidFunctionsFunctionNameRouteWithChildren
}

const AuthRouteChildren: AuthRouteChildren = {
  AuthSettingsSplatRoute: AuthSettingsSplatRoute,
  AuthProjectsIndexRoute: AuthProjectsIndexRoute,
  AuthProjectsProjectUuidPlaygroundRouteRoute:
    AuthProjectsProjectUuidPlaygroundRouteRouteWithChildren,
  AuthProjectsProjectsProjectUuidRoute: AuthProjectsProjectsProjectUuidRoute,
  AuthProjectsProjectUuidIndexRoute: AuthProjectsProjectUuidIndexRoute,
  AuthProjectsProjectUuidTracesSplatRoute:
    AuthProjectsProjectUuidTracesSplatRoute,
  AuthProjectsProjectUuidAnnotationsIndexRoute:
    AuthProjectsProjectUuidAnnotationsIndexRoute,
  AuthProjectsProjectUuidFunctionsIndexRoute:
    AuthProjectsProjectUuidFunctionsIndexRoute,
  AuthProjectsProjectUuidFunctionsFunctionNameRoute:
    AuthProjectsProjectUuidFunctionsFunctionNameRouteWithChildren,
}

const AuthRouteWithChildren = AuthRoute._addFileChildren(AuthRouteChildren)

export interface FileRoutesByFullPath {
  '/': typeof IndexRoute
  '': typeof AuthRouteWithChildren
  '/auth/callback': typeof AuthCallbackRoute
  '/auth/login': typeof AuthLoginRoute
  '/join/$token': typeof JoinTokenRoute
  '/settings/$': typeof AuthSettingsSplatRoute
  '/projects': typeof AuthProjectsIndexRoute
  '/projects/$projectUuid/playground': typeof AuthProjectsProjectUuidPlaygroundRouteRouteWithChildren
  '/projects/projects/$projectUuid': typeof AuthProjectsProjectsProjectUuidRoute
  '/projects/$projectUuid': typeof AuthProjectsProjectUuidIndexRoute
  '/projects/$projectUuid/traces/$': typeof AuthProjectsProjectUuidTracesSplatRoute
  '/projects/$projectUuid/annotations': typeof AuthProjectsProjectUuidAnnotationsIndexRoute
  '/projects/$projectUuid/functions': typeof AuthProjectsProjectUuidFunctionsIndexRoute
  '/projects/$projectUuid/functions/$functionName': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteWithChildren
  '/projects/$projectUuid/playground/$functionName': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteWithChildren
  '/projects/$projectUuid/playground/$functionName/': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute
  '/projects/$projectUuid/functions/$functionName/$functionUuid/$tab': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute
  '/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid': typeof AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute
  '/projects/$projectUuid/playground/$functionName/$functionUuid': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute
  '/projects/$projectUuid/functions/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid/$tab': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute
}

export interface FileRoutesByTo {
  '/': typeof IndexRoute
  '': typeof AuthRouteWithChildren
  '/auth/callback': typeof AuthCallbackRoute
  '/auth/login': typeof AuthLoginRoute
  '/join/$token': typeof JoinTokenRoute
  '/settings/$': typeof AuthSettingsSplatRoute
  '/projects': typeof AuthProjectsIndexRoute
  '/projects/$projectUuid/playground': typeof AuthProjectsProjectUuidPlaygroundRouteRouteWithChildren
  '/projects/projects/$projectUuid': typeof AuthProjectsProjectsProjectUuidRoute
  '/projects/$projectUuid': typeof AuthProjectsProjectUuidIndexRoute
  '/projects/$projectUuid/traces/$': typeof AuthProjectsProjectUuidTracesSplatRoute
  '/projects/$projectUuid/annotations': typeof AuthProjectsProjectUuidAnnotationsIndexRoute
  '/projects/$projectUuid/functions': typeof AuthProjectsProjectUuidFunctionsIndexRoute
  '/projects/$projectUuid/functions/$functionName': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteWithChildren
  '/projects/$projectUuid/playground/$functionName': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute
  '/projects/$projectUuid/functions/$functionName/$functionUuid/$tab': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute
  '/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid': typeof AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute
  '/projects/$projectUuid/playground/$functionName/$functionUuid': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute
  '/projects/$projectUuid/functions/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid/$tab': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/': typeof IndexRoute
  '/_auth': typeof AuthRouteWithChildren
  '/auth/callback': typeof AuthCallbackRoute
  '/auth/login': typeof AuthLoginRoute
  '/join/$token': typeof JoinTokenRoute
  '/_auth/settings/$': typeof AuthSettingsSplatRoute
  '/_auth/projects/': typeof AuthProjectsIndexRoute
  '/_auth/projects/$projectUuid/playground': typeof AuthProjectsProjectUuidPlaygroundRouteRouteWithChildren
  '/_auth/projects/projects/$projectUuid': typeof AuthProjectsProjectsProjectUuidRoute
  '/_auth/projects/$projectUuid/': typeof AuthProjectsProjectUuidIndexRoute
  '/_auth/projects/$projectUuid/traces/$': typeof AuthProjectsProjectUuidTracesSplatRoute
  '/_auth/projects/$projectUuid/annotations/': typeof AuthProjectsProjectUuidAnnotationsIndexRoute
  '/_auth/projects/$projectUuid/functions/': typeof AuthProjectsProjectUuidFunctionsIndexRoute
  '/_auth/projects/$projectUuid/functions/$functionName': typeof AuthProjectsProjectUuidFunctionsFunctionNameRouteWithChildren
  '/_auth/projects/$projectUuid/functions/$functionName/_workbench': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchRouteRouteWithChildren
  '/_auth/projects/$projectUuid/playground/$functionName': typeof AuthProjectsProjectUuidPlaygroundFunctionNameRouteWithChildren
  '/_auth/projects/$projectUuid/playground/$functionName/_layout': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutRouteWithChildren
  '/_auth/projects/$projectUuid/playground/$functionName/_layout/': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutIndexRoute
  '/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchFunctionUuidTabRoute
  '/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid': typeof AuthProjectsProjectUuidPlaygroundFunctionNameCompareFirstFunctionUuidSecondFunctionUuidRoute
  '/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/': typeof AuthProjectsProjectUuidPlaygroundFunctionNameLayoutFunctionUuidIndexRoute
  '/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab': typeof AuthProjectsProjectUuidFunctionsFunctionNameWorkbenchCompareFirstFunctionUuidSecondFunctionUuidTabRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths:
    | '/'
    | ''
    | '/auth/callback'
    | '/auth/login'
    | '/join/$token'
    | '/settings/$'
    | '/projects'
    | '/projects/$projectUuid/playground'
    | '/projects/projects/$projectUuid'
    | '/projects/$projectUuid'
    | '/projects/$projectUuid/traces/$'
    | '/projects/$projectUuid/annotations'
    | '/projects/$projectUuid/functions'
    | '/projects/$projectUuid/functions/$functionName'
    | '/projects/$projectUuid/playground/$functionName'
    | '/projects/$projectUuid/playground/$functionName/'
    | '/projects/$projectUuid/functions/$functionName/$functionUuid/$tab'
    | '/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid'
    | '/projects/$projectUuid/playground/$functionName/$functionUuid'
    | '/projects/$projectUuid/functions/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid/$tab'
  fileRoutesByTo: FileRoutesByTo
  to:
    | '/'
    | ''
    | '/auth/callback'
    | '/auth/login'
    | '/join/$token'
    | '/settings/$'
    | '/projects'
    | '/projects/$projectUuid/playground'
    | '/projects/projects/$projectUuid'
    | '/projects/$projectUuid'
    | '/projects/$projectUuid/traces/$'
    | '/projects/$projectUuid/annotations'
    | '/projects/$projectUuid/functions'
    | '/projects/$projectUuid/functions/$functionName'
    | '/projects/$projectUuid/playground/$functionName'
    | '/projects/$projectUuid/functions/$functionName/$functionUuid/$tab'
    | '/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid'
    | '/projects/$projectUuid/playground/$functionName/$functionUuid'
    | '/projects/$projectUuid/functions/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid/$tab'
  id:
    | '__root__'
    | '/'
    | '/_auth'
    | '/auth/callback'
    | '/auth/login'
    | '/join/$token'
    | '/_auth/settings/$'
    | '/_auth/projects/'
    | '/_auth/projects/$projectUuid/playground'
    | '/_auth/projects/projects/$projectUuid'
    | '/_auth/projects/$projectUuid/'
    | '/_auth/projects/$projectUuid/traces/$'
    | '/_auth/projects/$projectUuid/annotations/'
    | '/_auth/projects/$projectUuid/functions/'
    | '/_auth/projects/$projectUuid/functions/$functionName'
    | '/_auth/projects/$projectUuid/functions/$functionName/_workbench'
    | '/_auth/projects/$projectUuid/playground/$functionName'
    | '/_auth/projects/$projectUuid/playground/$functionName/_layout'
    | '/_auth/projects/$projectUuid/playground/$functionName/_layout/'
    | '/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab'
    | '/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid'
    | '/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/'
    | '/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  IndexRoute: typeof IndexRoute
  AuthRoute: typeof AuthRouteWithChildren
  AuthCallbackRoute: typeof AuthCallbackRoute
  AuthLoginRoute: typeof AuthLoginRoute
  JoinTokenRoute: typeof JoinTokenRoute
}

const rootRouteChildren: RootRouteChildren = {
  IndexRoute: IndexRoute,
  AuthRoute: AuthRouteWithChildren,
  AuthCallbackRoute: AuthCallbackRoute,
  AuthLoginRoute: AuthLoginRoute,
  JoinTokenRoute: JoinTokenRoute,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/",
        "/_auth",
        "/auth/callback",
        "/auth/login",
        "/join/$token"
      ]
    },
    "/": {
      "filePath": "index.tsx"
    },
    "/_auth": {
      "filePath": "_auth.tsx",
      "children": [
        "/_auth/settings/$",
        "/_auth/projects/",
        "/_auth/projects/$projectUuid/playground",
        "/_auth/projects/projects/$projectUuid",
        "/_auth/projects/$projectUuid/",
        "/_auth/projects/$projectUuid/traces/$",
        "/_auth/projects/$projectUuid/annotations/",
        "/_auth/projects/$projectUuid/functions/",
        "/_auth/projects/$projectUuid/functions/$functionName"
      ]
    },
    "/auth/callback": {
      "filePath": "auth.callback.tsx"
    },
    "/auth/login": {
      "filePath": "auth.login.tsx"
    },
    "/join/$token": {
      "filePath": "join.$token.tsx"
    },
    "/_auth/settings/$": {
      "filePath": "_auth/settings.$.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/": {
      "filePath": "_auth/projects/index.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/$projectUuid/playground": {
      "filePath": "_auth/projects/$projectUuid/playground/route.tsx",
      "parent": "/_auth",
      "children": [
        "/_auth/projects/$projectUuid/playground/$functionName"
      ]
    },
    "/_auth/projects/projects/$projectUuid": {
      "filePath": "_auth/projects/projects.$projectUuid.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/$projectUuid/": {
      "filePath": "_auth/projects/$projectUuid.index.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/$projectUuid/traces/$": {
      "filePath": "_auth/projects/$projectUuid/traces.$.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/$projectUuid/annotations/": {
      "filePath": "_auth/projects/$projectUuid/annotations/index.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/$projectUuid/functions/": {
      "filePath": "_auth/projects/$projectUuid/functions/index.tsx",
      "parent": "/_auth"
    },
    "/_auth/projects/$projectUuid/functions/$functionName": {
      "filePath": "_auth/projects/$projectUuid/functions/$functionName/_workbench",
      "parent": "/_auth",
      "children": [
        "/_auth/projects/$projectUuid/functions/$functionName/_workbench"
      ]
    },
    "/_auth/projects/$projectUuid/functions/$functionName/_workbench": {
      "filePath": "_auth/projects/$projectUuid/functions/$functionName/_workbench/route.tsx",
      "parent": "/_auth/projects/$projectUuid/functions/$functionName",
      "children": [
        "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab",
        "/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab"
      ]
    },
    "/_auth/projects/$projectUuid/playground/$functionName": {
      "filePath": "_auth/projects/$projectUuid/playground/$functionName",
      "parent": "/_auth/projects/$projectUuid/playground",
      "children": [
        "/_auth/projects/$projectUuid/playground/$functionName/_layout",
        "/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid"
      ]
    },
    "/_auth/projects/$projectUuid/playground/$functionName/_layout": {
      "filePath": "_auth/projects/$projectUuid/playground/$functionName/_layout.tsx",
      "parent": "/_auth/projects/$projectUuid/playground/$functionName",
      "children": [
        "/_auth/projects/$projectUuid/playground/$functionName/_layout/",
        "/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/"
      ]
    },
    "/_auth/projects/$projectUuid/playground/$functionName/_layout/": {
      "filePath": "_auth/projects/$projectUuid/playground/$functionName/_layout/index.tsx",
      "parent": "/_auth/projects/$projectUuid/playground/$functionName/_layout"
    },
    "/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid/$tab": {
      "filePath": "_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.tsx",
      "parent": "/_auth/projects/$projectUuid/functions/$functionName/_workbench"
    },
    "/_auth/projects/$projectUuid/playground/$functionName/compare/$firstFunctionUuid/$secondFunctionUuid": {
      "filePath": "_auth/projects/$projectUuid/playground/$functionName/compare.$firstFunctionUuid.$secondFunctionUuid.tsx",
      "parent": "/_auth/projects/$projectUuid/playground/$functionName"
    },
    "/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/": {
      "filePath": "_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid.index.tsx",
      "parent": "/_auth/projects/$projectUuid/playground/$functionName/_layout"
    },
    "/_auth/projects/$projectUuid/functions/$functionName/_workbench/compare/$firstFunctionUuid/$secondFunctionUuid/$tab": {
      "filePath": "_auth/projects/$projectUuid/functions/$functionName/_workbench/compare.$firstFunctionUuid.$secondFunctionUuid.$tab.tsx",
      "parent": "/_auth/projects/$projectUuid/functions/$functionName/_workbench"
    }
  }
}
ROUTE_MANIFEST_END */
