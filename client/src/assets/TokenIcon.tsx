import { LucideProps } from "lucide-react";
export const Token = (props: LucideProps) => {
  const {
    color = "currentColor",
    size = 24,
    strokeWidth = 2,
    className = "",
    ...otherProps
  } = props;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`lucide lucide-token ${className}`}
      {...otherProps}
    >
      {/* Outer circle (token border) */}
      <circle cx="12" cy="12" r="9" />
      {/* Central token element - hexagonal shape */}
      <path d="M12 7l4 2v6l-4 2l-4-2V9l4-2z" />
    </svg>
  );
};
