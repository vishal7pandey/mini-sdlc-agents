# Component Library Documentation

## Overview

This component library is built with **React 18**, **TypeScript**, **Tailwind CSS**, and **Radix UI** primitives.
All components follow the design system defined in the UI/UX specification.

## Design Principles

- **Accessibility First**  
  Components are built to be keyboard-accessible and screen‑reader friendly and aim for WCAG 2.1 AA contrast.
- **Type Safety**  
  All components are written in TypeScript with strict typing.
- **Composable**  
  Small, focused components that can be combined into richer UIs.
- **Consistent**  
  Shared tokens (colors, spacing, typography) and an 8px spacing grid.

---

## Component Categories

### UI Primitives (`components/ui/`)

- **Button** – primary action trigger with variants and sizes.  
  File: `components/ui/button.tsx`
- **Input** – text input field with error state.  
  File: `components/ui/input.tsx`
- **Textarea** – multi‑line input with monospace styling.  
  File: `components/ui/textarea.tsx`
- **Label** – accessible label built on Radix `@radix-ui/react-label`.  
  File: `components/ui/label.tsx`
- **FormField** – groups label, control, helper/error text.  
  File: `components/ui/form-field.tsx`
- **Card** – surface container with header/body/footer.  
  File: `components/ui/card.tsx`
- **StatCard** – statistic card used on dashboards.  
  File: `components/ui/stat-card.tsx`
- **Tabs** – tabbed navigation built on `@radix-ui/react-tabs`.  
  File: `components/ui/tabs.tsx`
- **Dialog** – modal dialog built on `@radix-ui/react-dialog`.  
  File: `components/ui/dialog.tsx`

### Layout Components (`components/layout/`)

- **Navbar** – sticky top navigation bar.  
  File: `components/layout/navbar.tsx`
- **Sidebar** – agent/quick‑actions sidebar, desktop‑first.  
  File: `components/layout/sidebar.tsx`
- **PageLayout** – shared page header + scrollable body wrapper.  
  File: `components/layout/page-layout.tsx`

### Feature Components (`components/features/`)

Feature‑level components are higher‑order building blocks composed from primitives.

- **StatCard** – metric display (currently implemented in `components/ui/stat-card.tsx`).
- **AgentCard** – agent summary card (currently implemented inline inside `Sidebar`).
- **Future** (planned):
  - `PipelineFlow` – pipeline visualization.
  - `JSONViewer` – structured JSON view.
  - `LogViewer` – streaming logs.

---

## Usage Examples

### Button

```tsx
import { Button } from "@/components/ui/button";

function Example() {
  return <Button type="submit">Submit</Button>;
}
```

**Props (partial)**

- `variant?: "primary" | "secondary" | "outline" | "ghost"`  
  Visual style of the button. Default: `"primary"`.
- `size?: "sm" | "default" | "lg" | "icon"`  
  Size of the button. Default: `"default"`.
- `asChild?: boolean`  
  When `true`, renders children via Radix `Slot` instead of a native `button`.
- All standard `React.ButtonHTMLAttributes<HTMLButtonElement>` (e.g. `type`, `disabled`, `onClick`).

---

### Input

```tsx
import { Input } from "@/components/ui/input";

function Example() {
  return <Input placeholder="Enter text..." />;
}
```

**Props**

- `error?: boolean` – when `true`, applies error border and focus ring.
- All standard `React.InputHTMLAttributes<HTMLInputElement>`.

---

### FormField

```tsx
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";

function Example({ error }: { error?: string }) {
  return (
    <FormField
      label="Email Address"
      required
      error={error}
      helperText="We'll never share your email"
    >
      <Input
        type="email"
        placeholder="you@example.com"
        error={Boolean(error)}
      />
    </FormField>
  );
}
```

**Props**

- `label: string` – label text.
- `required?: boolean` – shows red asterisk when `true`.
- `error?: string` – error message shown below the field.
- `helperText?: string` – helper text (hidden when `error` is present).
- `children: React.ReactNode` – usually an `Input` or `Textarea`.
- `className?: string` – to extend wrapper styling.

---

## Styling Guidelines

### Color Usage

- **Primary actions**: `bg-accent-primary`, hover `bg-accent-tertiary`.
- **Secondary actions**: `bg-bg-tertiary`, `border-border-primary`.
- **Surfaces**: `bg-bg-secondary` or `bg-bg-tertiary`.
- **Borders**: `border-border-primary`, `border-border-secondary`.
- **Text**: `text-text-primary`, `text-text-secondary`, `text-text-tertiary`.
- **Semantic**: `success`, `warning`, `error`, `info`, `agent-*` colors.

### Spacing

The system follows an **8px grid**:

- `xs = 4px`, `sm = 8px`, `md = 16px`, `lg = 24px`, `xl = 32px`.
- Prefer tokenized utilities such as:
  - `p-md`, `px-lg`, `py-sm`
  - `gap-md`, `gap-lg`
  - `mb-sm`, `mb-md`, `mb-lg`

### Responsive Design

- Mobile‑first.
- Tailwind breakpoints:
  - `sm = 640px`
  - `md = 768px`
  - `lg = 1024px`
  - `xl = 1280px`
- Use responsive grids such as:
  - `grid-cols-1 md:grid-cols-2 xl:grid-cols-4` for stat cards.

---

## Testing

- Unit tests live alongside components in `__tests__/` directories.
- Example: `components/ui/__tests__/button.test.tsx`, `components/ui/__tests__/input.test.tsx`.
- Run tests:

```bash
npm test
```

For coverage:

```bash
npm run test:coverage
```

Vitest + Testing Library are used for interaction‑focused, accessibility‑oriented tests.

---

## Accessibility

- All interactive elements are reachable via **keyboard**.
- Focus indicators use visible outlines/rings (`focus-visible:ring-*`).
- Radix primitives provide correct ARIA roles and attributes for dialogs, tabs, and labels.
- Color choices aim to meet **WCAG 2.1 AA** contrast.

When adding new components, prefer semantic HTML elements and verify keyboard behavior in the browser.
