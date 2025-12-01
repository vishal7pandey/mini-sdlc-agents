"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  // Base styles
  "inline-flex items-center justify-center rounded-md transition-colors duration-fast font-medium cursor-pointer disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary",
  {
    variants: {
      variant: {
        primary:
          "bg-accent-primary text-white hover:bg-accent-tertiary active:scale-[0.98]",
        secondary:
          "bg-bg-tertiary text-text-primary border border-border-primary hover:bg-bg-elevated hover:border-border-secondary",
        outline:
          "bg-transparent text-text-primary border border-border-primary hover:bg-bg-tertiary",
        ghost: "bg-transparent hover:bg-bg-tertiary",
      },
      size: {
        sm: "h-7 px-3 text-sm",
        default: "h-8 px-md text-base",
        lg: "h-10 px-5 text-lg",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";

export { Button, buttonVariants };
