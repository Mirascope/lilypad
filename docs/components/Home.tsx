import { CodeBlock } from "@/components/CodeBlock";
import { SlackLogo } from "@/components/SlackLogo";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Eye,
  GitCompare,
  LucideIcon,
  SquareCheckBig,
  Users,
} from "lucide-react";
import Link from "next/link";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  buttonText: string;
  buttonHref: string;
}

const FeatureCard = ({
  icon: Icon,
  title,
  description,
  buttonText,
  buttonHref,
}: FeatureCardProps) => (
  <div className="flex flex-col gap-4 bg-white rounded-lg p-6 shadow-md border border-slate-200">
    <Icon size="36" className="text-primary" />
    <h3 className="text-xl sm:text-2xl font-bold">{title}</h3>
    <p className="text-gray-700">{description}</p>
    <div className="mt-auto">
      <Link href={buttonHref}>
        <Button variant="outline" className="w-full">
          {buttonText}
          <ArrowRight />
        </Button>
      </Link>
    </div>
  </div>
);

export const Home = () => {
  const features: FeatureCardProps[] = [
    {
      icon: Eye,
      title: "Complete Visibility",
      description:
        "Monitor every aspect of your LLM applications with zero code changes. Track results, costs, and performance across all major LLM providers in a unified dashboard.",
      buttonText: "Learn about Tracing",
      buttonHref: "/docs/tracing/overview",
    },
    {
      icon: GitCompare,
      title: "Version Control for the LLM Era",
      description:
        "Traditional version control breaks with non-deterministic LLM outputs. Lilypad captures and versions all your prompts and LLM code into reproducible units, ensuring consistent results across environments.",
      buttonText: "Learn about Automatic Versioning",
      buttonHref: "/docs/versioning/overview",
    },
    {
      icon: SquareCheckBig,
      title: "Outcome-Based Quality Metrics",
      description:
        "Define and measure metrics that align LLM outputs with your business objectives. Seamlessly transition from human feedback to automated evaluations you can trust.",
      buttonText: "Learn about Evaluation",
      buttonHref: "/docs/evaluations",
    },
    {
      icon: Users,
      title: "Collaboration Without Chaos",
      description:
        "Enable business users to safely modify prompts through a playground while changes automatically sync with your codebase. Built-in guardrails prevent breaking changes without developer intervention.",
      buttonText: "Learn about Managed Generations",
      buttonHref: "/docs/versioning/managed-generations",
    },
  ];

  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="py-16 md:py-24 flex flex-col gap-8 items-center justify-center text-center px-4 max-w-6xl mx-auto">
        <div className="animate-fade-in-up">
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold mb-8">
            <span className="text-primary">Lilypad</span>: Open-Source
            <br />
            AI Engineering Platform
          </h1>
          <p className="text-lg sm:text-xl max-w-3xl mx-auto text-gray-700">
            Enable seamless collaboration between developers, business users,
            and domain experts while maintaining quality and reproducibility in
            your AI applications.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up animation-delay-200">
          <Link href="/docs/quickstart">
            <Button size="lg">Quickstart</Button>
          </Link>
          <a
            href="https://github.com/Mirascope/lilypad"
            className="no-underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" size="lg">
              <svg
                role="img"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <title>GitHub</title>
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
              Star us on GitHub
            </Button>
          </a>
          <a
            href="https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA"
            className="no-underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" size="lg">
              <SlackLogo width="24" height="24" />
              <span className="ml-2">Community</span>
            </Button>
          </a>
        </div>

        {/* Code Example */}
        <CodeBlock
          code={`import os

import lilypad
from openai import OpenAI

os.environ["LILYPAD_PROJECT_ID"] = "..."
os.environ["LILYPAD_API_KEY"] = "..."
os.environ["OPENAI_API_KEY"] = "..."

lilypad.configure()    # Automatically trace LLM API calls
client = OpenAI()


@lilypad.generation()  # Automatically version non-deterministic functions
def answer_question(question: str) -> str | None:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Answer this question: {question}"},
        ],
    )
    return completion.choices[0].message.content


answer = answer_question("What is the capital of France?")
print(answer)
# > The capital of France is Paris.`}
          language="python"
          filename="answer_question.py"
          highlightLines={[3, 6, 7, 10, 14]}
        />
      </section>

      {/* Features Section */}
      <section className="py-8">
        <h2 className="text-2xl text-center sm:text-4xl font-bold mb-6">
          All the tools you need for the
          <br />
          entire LLM development lifecycle
        </h2>
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 mb-16">
            {features.map((feature, index) => (
              <FeatureCard key={index} {...feature} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="pb-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl sm:text-4xl font-bold mb-6">
            Start using Lilypad today for free!
          </h2>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/docs/quickstart">
              <Button size="lg">Get Started</Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
};
