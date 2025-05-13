import { Link } from "@tanstack/react-router";

export function ForbiddenBoundary() {
  return (
    <div className="min-w-0 flex-1 p-4 flex flex-col items-center justify-center gap-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-red-600 mb-2">Access Denied</h1>
        <p className="text-gray-700 dark:text-gray-300 mb-4">
          You don&apos;t have permission to access this resource. You may need
          to upgrade your plan to access this feature.
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          If you believe this is an error, please contact william@mirascope.com.
        </p>
      </div>
      <div className="flex gap-2 items-center flex-wrap">
        <Link
          to="/settings/$"
          params={{ _splat: "overview" }}
          className={`px-2 py-1 bg-primary dark:bg-primary rounded text-white uppercase font-extrabold`}
        >
          Upgrade
        </Link>
        <Link
          to="/"
          className={`px-2 py-1 bg-gray-600 dark:bg-gray-700 rounded text-white uppercase font-extrabold`}
        >
          Home
        </Link>
      </div>
    </div>
  );
}
