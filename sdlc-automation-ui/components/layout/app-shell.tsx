import type { ReactNode } from "react";

export type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50">
      {children}
    </div>
  );
}
