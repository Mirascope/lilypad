import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSearch } from "@/hooks/use-search";
import { FormEvent, useState } from "react";

interface SearchComponentProps {
  projectUuid: string;
}
export const SearchComponent = ({ projectUuid }: SearchComponentProps) => {
  const { search } = useSearch(projectUuid);

  const [inputValue, setInputValue] = useState("");

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    search(inputValue);
  };

  return (
    <div>
      <form onSubmit={handleSearch}>
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder='Search spans...'
        />
        <Button type='submit'>Search</Button>
      </form>
    </div>
  );
};
