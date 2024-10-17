import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { FieldError, Merge, FieldErrorsImpl } from "react-hook-form";
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type ErrorMessage =
  | string
  | FieldError
  | Merge<FieldError, FieldErrorsImpl<any>>
  | undefined;

export const getErrorMessage = (error: ErrorMessage): string | undefined => {
  if (typeof error === "string") {
    return error;
  }
  if (error && "message" in error) {
    return error.message as string;
  }
  return undefined;
};
