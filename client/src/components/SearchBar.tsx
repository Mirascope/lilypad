import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSearch } from "@/hooks/use-search";
import { SpanPublic } from "@/types/types";
import { settingsQueryOptions } from "@/utils/settings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Loader, Search, X } from "lucide-react";
import { useEffect, useState } from "react";

export const SearchBar = ({
  projectUuid,
  onDataChange,
  filterFunction,
}: {
  projectUuid: string;
  onDataChange: (data: SpanPublic[] | null) => void;
  filterFunction?: (data: SpanPublic[]) => SpanPublic[];
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const { spans: searchResults, isLoading, search } = useSearch(projectUuid);
  const { data: settings } = useSuspenseQuery(settingsQueryOptions());
  useEffect(() => {
    if (searchResults) {
      const filtered = filterFunction?.(searchResults) ?? searchResults;
      onDataChange(filtered);
    } else {
      onDataChange(null);
    }
  }, [searchResults, onDataChange]);

  const displayCount =
    searchResults && filterFunction
      ? filterFunction(searchResults).length
      : (searchResults?.length ?? 0);

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    search(searchQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    search("");
  };
  if (!settings.experimental) return null;
  return (
    <form onSubmit={handleSearchSubmit}>
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        {/* Search input and button */}
        <div className="relative grow">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            <Search size={16} />
          </div>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search spans..."
            disabled={isLoading}
            className="pl-10 pr-10 w-full h-10 focus-visible:ring-primary"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              type="button"
              onClick={handleClearSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 h-6 w-6"
              aria-label="Clear search"
            >
              <X size={16} />
            </Button>
          )}
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          className="bg-primary hover:bg-primary/90 text-white h-10 px-4 min-w-[100px]"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <Loader size={16} className="animate-spin" />
              Searching...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              Search
            </span>
          )}
        </Button>
      </div>

      {/* Results counter */}
      {searchResults && (
        <div className="mt-3 flex items-center justify-between border-t border-gray-200 pt-3">
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="bg-gray-50 text-gray-700 font-medium"
            >
              {displayCount} results found
            </Badge>
          </div>

          {searchResults.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearSearch}
              className="text-gray-500 hover:text-gray-700 text-sm"
            >
              <X size={14} className="mr-1" />
              Clear results
            </Button>
          )}
        </div>
      )}
    </form>
  );
};
