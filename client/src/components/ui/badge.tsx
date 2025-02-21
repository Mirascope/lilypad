import * as React from "react";

const badgeVariants = {
  variant: {
    default:
      "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
    secondary:
      "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
    destructive:
      "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
    outline: "text-foreground",
  },
  size: {
    default: "px-2.5 py-0.5 text-xs",
    sm: "px-2 py-0.5 text-[10px]",
  },
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof badgeVariants.variant;
  size?: keyof typeof badgeVariants.size;
}

function Badge({
  className = "",
  variant = "default",
  size = "default",
  ...props
}: BadgeProps) {
  const baseClasses =
    "inline-flex items-center rounded-md border font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";
  const variantClasses = badgeVariants.variant[variant];
  const sizeClasses = badgeVariants.size[size];

  const combinedClasses = `${baseClasses} ${variantClasses} ${sizeClasses} ${className}`;

  return <div className={combinedClasses} {...props} />;
}

export { Badge, badgeVariants };
