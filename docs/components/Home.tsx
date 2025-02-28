import { SlackLogo } from "@/components/SlackLogo";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export const Home = () => {
  return (
    <main className="h-[calc(100vh-229px)] justify-center flex flex-col grow mx-auto px-4 max-w-6xl">
      <section className="py-12 md:py-20 text-center">
        <h1 className="whitespace-nowrap text-2xl sm:text-5xl lg:text-6xl font-bold mb-6 animate-fade-in-up">
          <p>Engineer Your Prompts.</p>
          <p className="text-primary">Automate Your Data Flywheel.</p>
        </h1>
        <div className="text-sm sm:text-xl mb-8 animate-fade-in-up animation-delay-200">
          <p>Build your LLM-powered application.</p>
          <p>
            <b>Lilypad helps make it great</b>,{" "}
            <em>so you can ship with confidence</em>.
          </p>
        </div>
        <div className="flex flex-col gap-y-4 sm:gap-y-0 sm:flex-row justify-center sm:space-x-4">
          <Link href="/docs">
            <Button size="lg" className="sm:w-fit w-full">
              Read the docs
            </Button>
          </Link>
          <a
            href="https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA"
            className="no-underline"
          >
            <Button variant="secondary" size="lg" className="sm:w-fit w-full border">
              <SlackLogo width="18" height="18" />
              Community
            </Button>
          </a>
        </div>
      </section>
    </main>
  );
};
