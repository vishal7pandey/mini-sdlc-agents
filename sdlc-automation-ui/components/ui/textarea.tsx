"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "w-full min-h-[120px] px-md py-3 rounded-md resize-y transition-colors duration-fast",
          "bg-bg-tertiary border border-border-primary",
          "text-text-primary placeholder:text-text-tertiary",
          "font-mono text-sm leading-relaxed",
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

Textarea.displayName = "Textarea";

export { Textarea };
