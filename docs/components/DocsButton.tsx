import Link from "next/link";
import { Button } from "@/components/ui/button";

export const DocsButton = () => {
  return (
    <Link href="/docs">
      <Button size="lg" className="sm:w-fit w-full">
        Read the docs
      </Button>
    </Link>
  );
};
