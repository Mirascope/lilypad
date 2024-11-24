import { useState, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

export const NewsletterSignup = () => {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle"); // idle, loading, success, error
  const formRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    setStatus("loading");

    try {
      formRef.current?.submit();
      setStatus("success");
      setEmail("");
    } catch (error) {
      setStatus("error");
      console.error("Newsletter signup error:", error);
    }
  };

  return (
    <div className="max-w-3xl mx-auto text-center flex flex-col items-center">
      <h2 className="text-md sm:text-lg font-bold mb-6">
        Join our newsletter for updates and a chance
        <br />
        to get early access to our closed beta
      </h2>

      {status === "success" ? (
        <Alert className="bg-green-50 border-green-200 mb-4 w-fit">
          <AlertDescription className="text-green-800">
            Thanks for joining! Please check your email to confirm.
          </AlertDescription>
        </Alert>
      ) : (
        <form
          ref={formRef}
          className="flex items-center justify-center space-x-2"
          action="https://newsletter.lilypad.so/api/v1/free?nojs=true"
          method="POST"
          target="hidden_iframe"
          onSubmit={handleSubmit}
        >
          <input
            type="hidden"
            name="first_url"
            value={typeof window !== "undefined" ? window.location.href : ""}
          />
          <input type="hidden" name="first_referrer" value="" />
          <input
            type="hidden"
            name="current_url"
            value={typeof window !== "undefined" ? window.location.href : ""}
          />
          <input type="hidden" name="current_referrer" value="" />
          <input type="hidden" name="referral_code" value="" />
          <input type="hidden" name="source" value="cover_page" />
          <input type="hidden" name="referring_pub_id" value="" />
          <input type="hidden" name="additional_referring_pub_ids" value="" />

          <Input
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="w-64 sm:w-80"
            required
            disabled={status === "loading"}
          />
          <Button type="submit" disabled={status === "loading"}>
            {status === "loading" ? "Joining..." : "Join"}
          </Button>
        </form>
      )}

      {status === "error" && (
        <Alert className="bg-red-100 mt-4 w-fit">
          <AlertDescription className="text-red-800">
            Failed to subscribe. Please try again later.
          </AlertDescription>
        </Alert>
      )}

      {/* Hidden iframe for form submission */}
      <iframe
        name="hidden_iframe"
        id="hidden_iframe"
        style={{ display: "none" }}
      />
    </div>
  );
};
