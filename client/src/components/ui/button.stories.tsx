import { Button } from "@/components/ui/button";
import type { Meta, StoryObj } from "@storybook/react";
import { ArrowRight, Mail } from "lucide-react";

const meta = {
  title: "UI/Button",
  component: Button,
  parameters: {
    layout: "centered",
  },
  argTypes: {
    variant: {
      control: "select",
      options: [
        "default",
        "destructive",
        "outline",
        "secondary",
        "ghost",
        "link",
      ],
      description: "The visual style of the button",
    },
    size: {
      control: "select",
      options: ["default", "sm", "lg", "icon"],
      description: "The size of the button",
    },
    asChild: {
      control: "boolean",
      description: "Whether to render as child or button element",
    },
    disabled: {
      control: "boolean",
      description: "Whether the button is disabled",
    },
  },
  // Use `args` to set default values for all stories
  args: {
    variant: "default",
    size: "default",
    asChild: false,
    disabled: false,
  },
  // Use `tags` for Storybook categorization
  tags: ["autodocs"],
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default: Story = {
  args: {
    children: "Button",
  },
};

export const Secondary: Story = {
  args: {
    variant: "secondary",
    children: "Secondary",
  },
};

export const Destructive: Story = {
  args: {
    variant: "destructive",
    children: "Destructive",
  },
};

export const Outline: Story = {
  args: {
    variant: "outline",
    children: "Outline",
  },
};

export const Ghost: Story = {
  args: {
    variant: "ghost",
    children: "Ghost",
  },
};

export const Link: Story = {
  args: {
    variant: "link",
    children: "Link Button",
  },
};

export const Small: Story = {
  args: {
    size: "sm",
    children: "Small",
  },
};

export const Large: Story = {
  args: {
    size: "lg",
    children: "Large",
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: "Disabled",
  },
};

export const WithIcon: Story = {
  args: {
    children: (
      <>
        <Mail />
        Email
      </>
    ),
  },
};

export const IconOnly: Story = {
  args: {
    size: "icon",
    "aria-label": "Send email",
    children: <Mail />,
  },
};

export const WithTrailingIcon: Story = {
  args: {
    children: (
      <>
        Next
        <ArrowRight />
      </>
    ),
  },
};

// You can create variations with specific controls to demonstrate additional use cases
export const AsLink: Story = {
  args: {
    variant: "link",
    asChild: true,
    children: <a href="#">Link styled as button</a>,
  },
};

/**
 * More complex example showing multiple buttons in different states.
 */
export const ButtonGroup: Story = {
  render: () => (
    <div className="flex flex-row gap-2">
      <Button variant="default">Default</Button>
      <Button variant="destructive">Delete</Button>
      <Button variant="outline">Cancel</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: "A group of buttons with different variants for comparison.",
      },
    },
  },
};

/**
 * Control states example
 */
export const ControlStates: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-4 gap-4">
        <Button>Default</Button>
        <Button disabled>Disabled</Button>
        <Button variant="destructive">Destructive</Button>
        <Button variant="destructive" disabled>
          Destructive Disabled
        </Button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Button variant="outline">Outline</Button>
        <Button variant="outline" disabled>
          Outline Disabled
        </Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="secondary" disabled>
          Secondary Disabled
        </Button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Button variant="ghost">Ghost</Button>
        <Button variant="ghost" disabled>
          Ghost Disabled
        </Button>
        <Button variant="link">Link</Button>
        <Button variant="link" disabled>
          Link Disabled
        </Button>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "A grid showing all button variants in their default and disabled states.",
      },
    },
  },
};
