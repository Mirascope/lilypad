import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Meta, StoryObj } from "@storybook/react";
import {
  ArrowRight,
  CalendarIcon,
  CreditCard,
  LineChart,
  MoreHorizontal,
  Package,
  Settings,
  UserRound,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./card";

const meta = {
  title: "UI/Card",
  component: Card,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic card with all components
export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card Description</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card Content</p>
      </CardContent>
      <CardFooter>
        <p>Card Footer</p>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "A basic card with all standard components: header, title, description, content, and footer.",
      },
    },
  },
};

// Simple sign-in form card
export const SignInForm: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Sign In</CardTitle>
        <CardDescription>
          Enter your credentials to access your account.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" placeholder="Your email address" />
            </div>
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Your password"
              />
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Sign In</Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: "A card with a simple sign-in form.",
      },
    },
  },
};

// Dashboard Card
export const DashboardCard: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
        <LineChart className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">$45,231.89</div>
        <p className="text-xs text-muted-foreground">+20.1% from last month</p>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: "A dashboard metric card with an icon and compact layout.",
      },
    },
  },
};

// Card with Tabs
export const CardWithTabs: Story = {
  render: () => (
    <Card className="w-[400px]">
      <CardHeader>
        <CardTitle>Account Settings</CardTitle>
        <CardDescription>Manage your account preferences.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
          </TabsList>
          <TabsContent value="profile" className="pt-4">
            <div className="flex flex-col space-y-3">
              <div className="flex flex-col space-y-1.5">
                <Label htmlFor="name">Name</Label>
                <Input id="name" placeholder="Your name" />
              </div>
              <div className="flex flex-col space-y-1.5">
                <Label htmlFor="username">Username</Label>
                <Input id="username" placeholder="Your username" />
              </div>
            </div>
          </TabsContent>
          <TabsContent value="security" className="pt-4">
            <div className="flex flex-col space-y-3">
              <div className="flex flex-col space-y-1.5">
                <Label htmlFor="password">Current Password</Label>
                <Input id="password" type="password" />
              </div>
              <div className="flex flex-col space-y-1.5">
                <Label htmlFor="new-password">New Password</Label>
                <Input id="new-password" type="password" />
              </div>
            </div>
          </TabsContent>
          <TabsContent value="preferences" className="pt-4">
            <p>Preferences tab content</p>
          </TabsContent>
        </Tabs>
      </CardContent>
      <CardFooter className="flex justify-end">
        <Button>Save Changes</Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: "A card with embedded tabs for organizing content.",
      },
    },
  },
};

// Card with nested cards
export const NestedCards: Story = {
  render: () => (
    <Card className="w-[450px]">
      <CardHeader>
        <CardTitle>Project Overview</CardTitle>
        <CardDescription>Track your project metrics and tasks.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Tasks</CardTitle>
          </CardHeader>
          <CardContent className="pb-2">
            <div className="flex items-center justify-between">
              <p className="text-sm">12 tasks completed</p>
              <p className="text-sm text-muted-foreground">75%</p>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-secondary">
              <div className="h-full w-3/4 rounded-full bg-primary"></div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Budget</CardTitle>
          </CardHeader>
          <CardContent className="pb-2">
            <div className="flex items-center justify-between">
              <p className="text-sm">$24,500 spent</p>
              <p className="text-sm text-muted-foreground">60%</p>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-secondary">
              <div className="h-full w-3/5 rounded-full bg-primary"></div>
            </div>
          </CardContent>
        </Card>
      </CardContent>
      <CardFooter>
        <Button variant="outline" className="w-full">
          <span>View Detailed Report</span>
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "A card with nested card components for hierarchical information.",
      },
    },
  },
};

// Pricing Card
export const PricingCard: Story = {
  render: () => (
    <Card className="w-[300px]">
      <CardHeader>
        <CardTitle>Pro Plan</CardTitle>
        <CardDescription>For professional developers</CardDescription>
      </CardHeader>
      <CardContent className="text-center">
        <span className="text-4xl font-bold">$29</span>
        <span className="text-muted-foreground">/month</span>
        <ul className="mt-6 space-y-2 text-left">
          <li className="flex items-center">
            <Package className="mr-2 h-4 w-4 text-primary" />
            <span>10 projects</span>
          </li>
          <li className="flex items-center">
            <UserRound className="mr-2 h-4 w-4 text-primary" />
            <span>5 team members</span>
          </li>
          <li className="flex items-center">
            <CalendarIcon className="mr-2 h-4 w-4 text-primary" />
            <span>30-day revision history</span>
          </li>
          <li className="flex items-center">
            <CreditCard className="mr-2 h-4 w-4 text-primary" />
            <span>Priority support</span>
          </li>
        </ul>
      </CardContent>
      <CardFooter>
        <Button className="w-full">Subscribe</Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: "A pricing card with features list and subscription button.",
      },
    },
  },
};

// Card with hover and interaction effects
export const InteractiveCard: Story = {
  render: () => (
    <Card className="w-[350px] transition-all hover:shadow-lg hover:-translate-y-1 cursor-pointer">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Interactive Card</CardTitle>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>This card has hover and click effects</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Hover over or click this card to see interactive effects.</p>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline" size="sm">
          Cancel
        </Button>
        <Button size="sm">Continue</Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: "A card with hover effects and interactive elements.",
      },
    },
  },
};

// Horizontal Card Layout
export const HorizontalCard: Story = {
  render: () => (
    <Card className="flex flex-row w-[600px] overflow-hidden">
      <div className="w-1/3 bg-muted flex items-center justify-center">
        <div className="w-full h-full bg-muted flex items-center justify-center text-muted-foreground">
          <Settings className="h-10 w-10" />
        </div>
      </div>
      <div className="w-2/3">
        <CardHeader>
          <CardTitle>Horizontal Layout</CardTitle>
          <CardDescription>A card with a horizontal layout.</CardDescription>
        </CardHeader>
        <CardContent>
          <p>
            This card uses a horizontal layout with an image or icon section on
            the left.
          </p>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button variant="outline">Learn More</Button>
        </CardFooter>
      </div>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "A card with a horizontal layout instead of the default vertical arrangement.",
      },
    },
  },
};

// Card Grid
export const CardGrid: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 w-[650px]">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Card {i + 1}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs">Card in a responsive grid layout.</p>
          </CardContent>
        </Card>
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: "Multiple cards arranged in a responsive grid layout.",
      },
    },
  },
};
