import React from "react";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface AddCardButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string;
  onClick?: () => void;
}

export const AddCardButton: React.FC<AddCardButtonProps> = ({ className, onClick, ...props }) => {
  return (
    <Button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-[216px] w-64 shrink-0 items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-transparent transition-colors hover:border-gray-300 hover:bg-slate-50",
        className
      )}
      {...props}
    >
      <Plus className="h-6 w-6 text-gray-400" />
    </Button>
  );
};
