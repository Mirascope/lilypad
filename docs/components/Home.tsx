import { CommunityButton } from "./CommunityButton";
import { DocsButton } from "./DocsButton";

export const Home = () => {
  return (
    <main className="h-[calc(100vh-229px)] justify-center flex flex-col grow mx-auto px-4">
      <section className="py-20 text-center">
        <h1 className="whitespace-nowrap text-2xl sm:text-5xl lg:text-6xl font-bold mb-6 animate-fade-in-up">
          <p>Engineer Your Prompts.</p>
          <p className="text-primary">Automate Your Data Flywheel.</p>
        </h1>
        <div className="text-sm sm:text-xl mb-8 animate-fade-in-up animation-delay-200">
          <p>Build your LLM-powered application.</p>
          <p>
            <b>Lilypad handles the rest</b>,{" "}
            <em>so you can ship with confidence</em>.
          </p>
        </div>
        <div className="flex flex-col gap-y-4 sm:gap-y-0 sm:flex-row justify-center sm:space-x-4">
          <DocsButton />
          <CommunityButton />
        </div>
      </section>
    </main>
  );
};
