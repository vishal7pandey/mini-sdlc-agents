"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", error, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "w-full h-10 px-md rounded-md transition-colors duration-fast",
          "bg-bg-tertiary border border-border-primary",
          "text-text-primary placeholder:text-text-tertiary",
          "hover:bg-bg-elevated hover:border-border-secondary",
          "focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20",
          error &&
            "border-error focus:border-error focus:ring-error/20",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);

Input.displayName = "Input";

export { Input };
