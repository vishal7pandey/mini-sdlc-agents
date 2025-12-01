"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/ui/form-field";
import { Card, CardHeader, CardBody } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { cn } from "@/lib/utils";

export default function ComponentShowcase() {
  return (
    <div className="p-lg space-y-xl max-w-7xl mx-auto">
      <header className="space-y-sm">
        <h1 className="text-3xl font-semibold text-text-primary">
          Component Showcase
        </h1>
        <p className="text-base text-text-secondary">
          Interactive examples of all UI components in the design system.
        </p>
      </header>

      {/* Buttons */}
      <section>
        <h2 className="text-2xl font-semibold mb-md">Buttons</h2>
        <div className="space-y-md">
          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-sm">
              Variants
            </h3>
            <div className="flex flex-wrap gap-md">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-sm">
              Sizes
            </h3>
            <div className="flex flex-wrap gap-md items-center">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon" aria-label="Target">
                🎯
              </Button>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-sm">
              States
            </h3>
            <div className="flex flex-wrap gap-md items-center">
              <Button>Normal</Button>
              <Button disabled>Disabled</Button>
            </div>
          </div>
        </div>
      </section>

      {/* Form Fields */}
      <section>
        <h2 className="text-2xl font-semibold mb-md">Form Fields</h2>
        <div className="space-y-md max-w-lg">
          <FormField
            label="Text Input"
            required
            helperText="Enter your project title"
          >
            <Input placeholder="E-commerce Platform" />
          </FormField>

          <FormField label="With Error" error="This field is required">
            <Input error placeholder="Invalid input..." />
          </FormField>

          <FormField label="Textarea">
            <Textarea placeholder="Describe your requirements..." />
          </FormField>
        </div>
      </section>

      {/* Cards */}
      <section>
        <h2 className="text-2xl font-semibold mb-md">Cards</h2>
        <div className="grid gap-md md:grid-cols-2">
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-text-primary">Basic Card</h3>
            </CardHeader>
            <CardBody>
              <p className="text-text-secondary">Card content goes here.</p>
            </CardBody>
          </Card>

          <StatCard
            label="Metric Example"
            value="98.5%"
            change="↑ 5% increase"
            icon="✓"
            iconColor="bg-success/20 text-success"
          />
        </div>
      </section>

      {/* Color Palette */}
      <section>
        <h2 className="text-2xl font-semibold mb-md">Color Palette</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-md">
          <ColorSwatch color="bg-accent-primary" label="Accent Primary" />
          <ColorSwatch color="bg-agent-finalize" label="Agent Finalize" />
          <ColorSwatch color="bg-agent-design" label="Agent Design" />
          <ColorSwatch color="bg-agent-code" label="Agent Code" />
          <ColorSwatch color="bg-agent-test" label="Agent Test" />
          <ColorSwatch color="bg-success" label="Success" />
        </div>
      </section>
    </div>
  );
}

function ColorSwatch({
  color,
  label,
}: {
  color: string;
  label: string;
}) {
  return (
    <div className="flex flex-col">
      <div className={cn(color, "h-16 rounded-md mb-sm border border-border-primary")} />
      <span className="text-xs text-text-secondary">{label}</span>
    </div>
  );
}
