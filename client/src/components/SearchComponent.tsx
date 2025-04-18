import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSearch } from "@/hooks/use-search";
import { useState } from "react";

interface SearchComponentProps {
  projectUuid: string;
}
export const SearchComponent = ({ projectUuid }: SearchComponentProps) => {
  const { search } = useSearch(projectUuid);

  const [inputValue, setInputValue] = useState("");

  const handleSearch = () => {
    search(inputValue);
  };

  return (
    <div>
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder='Search spans...'
      />
      <Button onClick={handleSearch}>Search</Button>
    </div>
  );
};
