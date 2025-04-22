import { Loader2 } from "lucide-react";

interface SpinnerProps {
  size?: number;
  className?: string;
}

export const Spinner = ({ size = 20, className = "" }: SpinnerProps) => (
  <Loader2
    width={size}
    height={size}
    className={`animate-spin text-muted-foreground ${className}`}
  />
);
export default Spinner;
