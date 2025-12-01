import * as React from "react";

import { Card, CardBody } from "./card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  icon: React.ReactNode;
  iconColor?: string;
  className?: string;
}

export function StatCard({
  label,
  value,
  change,
  icon,
  iconColor = "bg-accent-primary/20 text-accent-primary",
  className,
}: StatCardProps) {
  return (
    <Card className={cn("min-w-[320px]", className)}>
      <CardBody className="flex items-start justify-between gap-md">
        <div className="space-y-xs">
          <div className="text-xs font-medium tracking-wide uppercase text-text-secondary">
            {label}
          </div>
          <div className="text-display font-bold text-text-primary mb-sm">
            {value}
          </div>
          {change && <div className="text-xs text-success">{change}</div>}
        </div>

        <div
          className={cn(
            "w-8 h-8 rounded-md flex items-center justify-center text-base",
            iconColor,
          )}
          aria-hidden="true"
        >
          {icon}
        </div>
      </CardBody>
    </Card>
  );
}
