"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/" },
  { label: "Requirements", href: "/requirements" },
  { label: "Pipeline", href: "/pipeline" },
  { label: "Telemetry", href: "/telemetry" },
  { label: "Settings", href: "/settings" },
] as const;

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 w-full h-[60px] bg-bg-secondary border-b border-border-primary shadow-sm">
      <div className="h-full px-lg flex items-center justify-between">
        {/* Left Section: Logo + Nav Tabs */}
        <div className="flex items-center gap-lg">
          <Link href="/" className="flex items-center gap-sm">
            <div className="flex h-9 w-9 items-center justify-center rounded-md overflow-hidden bg-bg-tertiary">
              <Image
                src="/icon.png"
                alt="Multi-Agent SDLC Automation"
                width={36}
                height={36}
                className="h-9 w-9"
              />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold text-text-primary">
                Cascade AI
              </span>
              <span className="text-xs text-text-secondary">
                SDLC Automation
              </span>
            </div>
          </Link>

          <div className="flex gap-sm">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "px-md py-sm rounded-md text-sm transition-fast",
                    isActive
                      ? "bg-accent-secondary text-white"
                      : "text-text-secondary hover:bg-bg-tertiary hover:text-text-primary",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Right Section: Status + Cost */}
        <div className="flex items-center gap-md">
          <div className="flex items-center gap-sm px-md py-sm bg-bg-tertiary rounded-md text-xs">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-text-secondary">All Systems Operational</span>
          </div>

          <div className="px-md py-sm bg-bg-tertiary rounded-md text-xs font-mono text-text-secondary">
            $0.42 / $10.00 daily
          </div>
        </div>
      </div>
    </nav>
  );
}
