"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/ui/form-field";
import { Card, CardHeader, CardBody } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";

export default function ComponentTest() {
  return (
    <main className="p-lg space-y-lg">
      <section>
        <h1 className="text-xl font-semibold mb-md">Button Variants</h1>
        <div className="flex flex-wrap gap-md items-center">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-md">Button Sizes</h2>
        <div className="flex flex-wrap gap-md items-center">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
          <Button size="icon" aria-label="Target icon">
            🎯
          </Button>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-md">Button States</h2>
        <div className="flex flex-wrap gap-md items-center">
          <Button disabled>Disabled</Button>
          <Button variant="secondary" disabled>
            Disabled Secondary
          </Button>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-md">Form Fields</h2>
        <div className="grid gap-lg md:grid-cols-2">
          <FormField
            label="Project name"
            required
            helperText="A short, human-readable name for your project."
          >
            <Input placeholder="Mini SDLC automation" />
          </FormField>

          <FormField
            label="Description"
            required
            helperText="Describe what you're trying to automate."
          >
            <Textarea placeholder="The system should..." />
          </FormField>

          <FormField
            label="With error"
            required
            error="This field is required."
          >
            <Input placeholder="Shows error state" error />
          </FormField>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-md">Cards</h2>
        <div className="grid gap-lg md:grid-cols-2">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-text-primary">
                Card Title
              </h3>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-text-secondary">
                Card content goes here. Use cards to group related information
                and actions.
              </p>
            </CardBody>
          </Card>

          <StatCard
            label="Requirements finalized"
            value="24"
            change="+12% vs last week"
            icon={"✓"}
          />
        </div>
      </section>
    </main>
  );
}
