import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Typography } from "@/components/ui/typography";
import { Dispatch, SetStateAction } from "react";

export const UserConsentDialog = ({
  open,
  setOpen,
  onClick,
}: {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  onClick: () => void;
}) => {
  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Terms of Service & Privacy Policy</AlertDialogTitle>
          <AlertDialogDescription>
            Please review and accept our terms before continuing.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <Typography variant="p" affects="muted">
          By signing in, you agree to our{" "}
          <a
            href="https://mirascope.com/terms/service"
            target="_blank"
            rel="noopener noreferrer"
            className="text-base text-primary no-underline hover:underline"
          >
            Terms of Service
          </a>{" "}
          and{" "}
          <a
            href="https://mirascope.com/privacy"
            target="_blank"
            rel="noopener noreferrer"
            className="text-base text-primary no-underline hover:underline"
          >
            Privacy Policy
          </a>
          .
        </Typography>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={onClick}>Continue</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
