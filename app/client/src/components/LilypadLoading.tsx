import { LilypadLogo } from "@/src/components/lilypad-logo";
import React from "react";
import { cn } from "../lib/utils";

interface LilypadLoadingProps {
  className?: string;
  size?: number;
  animation?: "rotate" | "pulse" | "both";
  iconClassName?: string;
}

export const LilypadLoading: React.FC<LilypadLoadingProps> = ({
  className,
  size = 96,
  animation = "pulse",
  iconClassName,
}) => {
  let animationClasses = "";
  if (animation === "rotate") {
    animationClasses = "animate-spin";
  } else if (animation === "pulse") {
    animationClasses = "animate-pulse";
  } else if (animation === "both") {
    animationClasses = "animate-spin animate-pulse";
  }

  return (
    <div className="inset-0 flex h-full items-center justify-center">
      <div
        className={cn("flex items-center justify-center", className)}
        style={{ width: size, height: size }}
      >
        <div className={cn("transform-gpu text-primary", animationClasses, iconClassName)}>
          <LilypadLogo width={`${size}`} height={`${size}`} />
        </div>
      </div>
    </div>
  );
};
