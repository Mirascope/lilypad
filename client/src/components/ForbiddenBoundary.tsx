import { Link } from "@tanstack/react-router";

export function ForbiddenBoundary() {
  return (
    <div className="flex min-w-0 flex-1 flex-col items-center justify-center gap-6 p-4">
      <div className="text-center">
        <h1 className="mb-2 text-3xl font-bold text-red-600">Access Denied</h1>
        <p className="mb-4 text-gray-700 dark:text-gray-300">
          You don&apos;t have permission to access this resource. You may need to upgrade your plan
          to access this feature.
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          If you believe this is an error, please contact william@mirascope.com.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Link
          to="/settings/$"
          params={{ _splat: "overview" }}
          className={`rounded bg-primary px-2 py-1 font-extrabold text-white uppercase dark:bg-primary`}
        >
          Upgrade
        </Link>
        <Link
          to="/"
          className={`rounded bg-gray-600 px-2 py-1 font-extrabold text-white uppercase dark:bg-gray-700`}
        >
          Home
        </Link>
      </div>
    </div>
  );
}
