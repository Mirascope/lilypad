import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/components/ui/button";
import { Calendar } from "@/src/components/ui/calendar";
import { Input } from "@/src/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/src/components/ui/popover";
import { useSearch } from "@/src/hooks/use-search";
import { cn } from "@/src/lib/utils";
import { SpanPublic } from "@/src/types/types";
import { format } from "date-fns";
import { CalendarIcon, Loader, Search, X } from "lucide-react";
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
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);

  const { spans: searchResults, isLoading, search, updateFilters } = useSearch(projectUuid);

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
    // Allow empty search query - the dates will be used as filters
    search(searchQuery.trim());
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setStartDate(undefined);
    setEndDate(undefined);
    search("");
    updateFilters({
      time_range_start: undefined,
      time_range_end: undefined,
    });
  };

  const handleStartDateChange = (date: Date | undefined) => {
    setStartDate(date);
    // Use milliseconds instead of seconds to match the backend expectation
    const timestamp = date ? date.getTime() : undefined;
    updateFilters({ time_range_start: timestamp });
  };

  const handleEndDateChange = (date: Date | undefined) => {
    setEndDate(date);
    // Add a day to include the entire end date (end of day) - in milliseconds
    const timestamp = date ? new Date(date.setHours(23, 59, 59, 999)).getTime() : undefined;
    updateFilters({ time_range_end: timestamp });
  };

  const clearStartDate = () => {
    setStartDate(undefined);
    updateFilters({ time_range_start: undefined });
  };

  const clearEndDate = () => {
    setEndDate(undefined);
    updateFilters({ time_range_end: undefined });
  };

  return (
    <form onSubmit={handleSearchSubmit}>
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        {/* Search input and button */}
        <div className="relative grow">
          <div className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400">
            <Search size={16} />
          </div>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search spans..."
            disabled={isLoading}
            className="h-10 w-full pr-10 pl-10 focus-visible:ring-primary"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              type="button"
              onClick={handleClearSearch}
              className="absolute top-1/2 right-2 h-6 w-6 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              aria-label="Clear search"
            >
              <X size={16} />
            </Button>
          )}
        </div>

        {/* Start Date Picker */}
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                "w-auto justify-start text-left font-normal",
                !startDate && "text-muted-foreground"
              )}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {startDate ? format(startDate, "PPP") : "Start date"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={startDate}
              onSelect={handleStartDateChange}
              autoFocus
            />
          </PopoverContent>
        </Popover>

        {/* End Date Picker */}
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                "w-auto justify-start text-left font-normal",
                !endDate && "text-muted-foreground"
              )}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {endDate ? format(endDate, "PPP") : "End date"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="end">
            <Calendar
              mode="single"
              selected={endDate}
              onSelect={handleEndDateChange}
              autoFocus
              disabled={(date) => (startDate ? date < startDate : false)}
            />
          </PopoverContent>
        </Popover>

        <Button
          type="submit"
          disabled={isLoading}
          className="h-10 min-w-[100px] bg-primary px-4 text-white hover:bg-primary/90"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <Loader size={16} className="animate-spin" />
              Searching...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              {!searchQuery.trim() && !startDate && !endDate ? "Show All" : "Search"}
            </span>
          )}
        </Button>
      </div>

      {/* Active filters and results counter */}
      {(searchResults ?? startDate ?? endDate) && (
        <div className="mt-3 flex items-center justify-between border-t border-gray-200 pt-3">
          <div className="flex flex-wrap items-center gap-2">
            {searchResults && (
              <Badge variant="outline" className="font-medium">
                {displayCount} results found
              </Badge>
            )}

            {startDate && (
              <Badge variant="secondary" className="flex items-center gap-1">
                From: {format(startDate, "PP")}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={clearStartDate}
                  className="ml-1 h-4 w-4 p-0"
                >
                  <X size={12} />
                </Button>
              </Badge>
            )}

            {endDate && (
              <Badge variant="secondary" className="flex items-center gap-1">
                To: {format(endDate, "PP")}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={clearEndDate}
                  className="ml-1 h-4 w-4 p-0"
                >
                  <X size={12} />
                </Button>
              </Badge>
            )}
          </div>

          {((searchResults && searchResults?.length > 0) ?? startDate ?? endDate) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearSearch}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              <X size={14} className="mr-1" />
              Clear all
            </Button>
          )}
        </div>
      )}
    </form>
  );
};
