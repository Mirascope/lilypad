/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        mirascope: "hsl(239, 84%, 67%)",
        "mirascope-light": "hsl(239, 84%, 75%)",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        chart: {
          1: "hsl(var(--chart-1))",
          2: "hsl(var(--chart-2))",
          3: "hsl(var(--chart-3))",
          4: "hsl(var(--chart-4))",
          5: "hsl(var(--chart-5))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      typography:
        '(theme) => ({\n        DEFAULT: {\n          css: {\n            code: {\n              fontSize: "inherit", // Remove any specific font size\n              fontFamily: "inherit", // Remove any specific font family\n              backgroundColor: "transparent", // Remove background color\n              padding: "0", // Remove padding\n              borderRadius: "0", // Remove border radius\n              color: "inherit", // Use inherited color\n            },\n            "code::before": {\n              content: "none", // Remove the `::before` element\n            },\n            "code::after": {\n              content: "none", // Remove the `::after` element\n            },\n          },\n        },\n      })',
    },
  },
  plugins: [
    require("tailwindcss-animate"),
    require("@tailwindcss/typography"),
    function ({ addBase, theme }) {
      addBase({
        ol: {
          listStyleType: "decimal",
          paddingLeft: "1.5em",
          marginTop: "1em",
          marginBottom: "1em",
        },
        ul: {
          listStyleType: "initial",
          paddingLeft: "1.5em",
          marginTop: "1em",
          marginBottom: "1em",
        },
        li: {
          marginTop: "0.5em",
          marginBottom: "0.5em",
        },
      });
    },
  ],
};
