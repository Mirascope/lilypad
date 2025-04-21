import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSearch } from "@/hooks/use-search";
import { SpanPublic } from "@/types/types";
import { Loader, Search, X } from "lucide-react";
import { useEffect, useState } from "react";

// Create a reusable SearchBar component
export const SearchBar = ({
  projectUuid,
  defaultData,
  onDataChange,
}: {
  projectUuid: string;
  defaultData: SpanPublic[];
  onDataChange: (data: SpanPublic[] | undefined) => void;
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const { spans: searchResults, isLoading, search } = useSearch(projectUuid);

  // Update parent component when search results change
  useEffect(() => {
    if (searchResults !== null) {
      onDataChange(searchResults);
    } else {
      onDataChange(defaultData);
    }
  }, [searchResults, defaultData, onDataChange]);

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    search(searchQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    search("");
  };

  return (
    <div className='px-2 pt-4'>
      <form onSubmit={handleSearchSubmit} className='flex gap-2'>
        <div className='relative flex-grow'>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder='Search spans...'
            disabled={isLoading}
            className='pr-10 w-full'
          />
          {searchResults && (
            <Button
              variant='ghost'
              size='icon'
              type='button'
              onClick={handleClearSearch}
              className='absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 h-6 w-6'
              aria-label='Clear search'
            >
              <X size={16} />
            </Button>
          )}
        </div>
        <Button
          type='submit'
          disabled={isLoading}
          className='bg-primary hover:bg-primary/80 text-white h-9'
        >
          {isLoading ? (
            <span className='flex items-center gap-2'>
              <Loader size={16} className='animate-spin' />
              Searching...
            </span>
          ) : (
            <span className='flex items-center gap-2'>
              <Search size={16} />
              Search
            </span>
          )}
        </Button>
      </form>

      {searchResults && (
        <div className='mt-2 text-sm text-gray-600'>
          Found {searchResults.length} results
        </div>
      )}
    </div>
  );
};
