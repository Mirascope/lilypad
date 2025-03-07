import { CheckCircle2, Mail } from "lucide-react";
import React from "react";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

export const Newsletter = () => {
  const [success, setSuccess] = React.useState(false);
  const [isClient, setIsClient] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Use useEffect to check if we're on client side
  React.useEffect(() => {
    setIsClient(true);

    // Check for success parameter in URL
    if (
      typeof window !== "undefined" &&
      window.location.search.includes("success=true")
    ) {
      setSuccess(true);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);

    // Prevent multiple submissions
    if (isSubmitting) return;

    setIsSubmitting(true);

    try {
      // Send data to the proxy endpoint
      const response = await fetch(
        "https://newsletter-signup-proxy.william-025.workers.dev",
        {
          method: "POST",
          body: formData,
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Subscription failed: ${response.statusText}`);
      }

      // Clear the form fields
      form.reset();

      // Update URL and state instead of reloading page
      const url = new URL(window.location.href);
      url.searchParams.set("success", "true");
      window.history.replaceState({}, document.title, url.toString());
      setSuccess(true);
    } catch (error) {
      console.error("Error submitting form:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseSuccess = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("success");
    window.history.replaceState({}, document.title, url.toString());
    setSuccess(false);
  };

  return (
    <main>
      <div className="flex flex-col items-center justify-center max-w-3xl mx-auto py-16 px-4">
        <Mail className="h-16 w-16 text-primary mb-6" />

        <h1 className="text-4xl font-bold mb-4 text-center">
          Subscribe to Our Newsletter
        </h1>

        <p className="text-xl text-gray-700 mb-10 text-center max-w-2xl">
          Stay updated with the latest features, guides, and news about Lilypad.
          We'll send occasional updates directly to your inbox.
        </p>

        <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8 border border-gray-200">
          <form onSubmit={handleSubmit} className="space-y-6">
            <input
              type="hidden"
              name="redirectTo"
              value="/newsletter?success=true"
            />

            <div className="space-y-2">
              <label
                htmlFor="firstName"
                className="block text-sm font-medium text-gray-700"
              >
                First Name
              </label>
              <Input
                id="firstName"
                type="text"
                name="firstName"
                placeholder="John"
                required
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <label
                htmlFor="lastName"
                className="block text-sm font-medium text-gray-700"
              >
                Last Name
              </label>
              <Input
                id="lastName"
                type="text"
                name="lastName"
                placeholder="Doe"
                required
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email address
              </label>
              <Input
                id="email"
                type="email"
                name="email"
                placeholder="you@example.com"
                required
                className="w-full"
              />
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Subscribing..." : "Subscribe"}
            </Button>

            <p className="text-xs text-gray-500 mt-4">
              By subscribing, you agree to receive marketing emails from us. You
              can unsubscribe at any time.
            </p>
          </form>
        </div>
      </div>
      {isClient && success && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <Alert className="bg-green-50 border-green-200 text-green-800">
              <CheckCircle2 className="h-5 w-5" />
              <AlertTitle>Success!</AlertTitle>
              <AlertDescription>
                Thank you for subscribing to our newsletter! You'll receive
                updates soon.
              </AlertDescription>
            </Alert>
            <div className="mt-4 flex justify-end">
              <Button onClick={handleCloseSuccess}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};
