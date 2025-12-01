import * as React from "react";

import { cn } from "@/lib/utils";

interface PageLayoutProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function PageLayout({
  title,
  subtitle,
  actions,
  children,
  className,
}: PageLayoutProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Page Header */}
      <header className="flex items-start justify-between px-lg pt-lg pb-md border-b border-border-primary">
        <div className="space-y-xs">
          <h1 className="text-3xl font-semibold text-text-primary">
            {title}
          </h1>
          {subtitle && (
            <p className="text-base text-text-secondary max-w-3xl">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="ml-md flex-shrink-0 flex items-center gap-sm">
            {actions}
          </div>
        )}
      </header>

      {/* Page Body */}
      <div className={cn("flex-1 p-lg overflow-y-auto", className)}>
        {children}
      </div>
    </div>
  );
}
