import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

interface Props extends HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

export const Caption = ({ className = "", children }: Props) => {
  return (
    <div className={cn("mt-2 text-xs text-gray-400 text-center", className)}>
      {children}
    </div>
  );
};

export default Caption;
