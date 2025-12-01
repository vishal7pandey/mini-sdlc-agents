"use client";

import { cn } from "@/lib/utils";
import { AGENTS, type Agent } from "@/types/agent";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui";

export function Sidebar() {
  const selectedAgentId = useUIStore((state) => state.selectedAgentId);
  const setSelectedAgentId = useUIStore((state) => state.setSelectedAgentId);

  return (
    <aside className="hidden md:block w-[280px] bg-bg-secondary border-r border-border-primary p-lg overflow-y-auto">
      {/* Active Agents Section */}
      <section className="mb-xl">
        <h3 className="text-xs uppercase tracking-wide text-text-tertiary mb-md font-semibold">
          Active Agents
        </h3>
        <div className="space-y-sm">
          {AGENTS.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              isActive={selectedAgentId === agent.id}
              onClick={() => setSelectedAgentId(agent.id)}
            />
          ))}
        </div>
      </section>

      {/* Quick Actions Section */}
      <section>
        <h3 className="text-xs uppercase tracking-wide text-text-tertiary mb-md font-semibold">
          Quick Actions
        </h3>
        <div className="space-y-sm">
          <Button variant="secondary" className="w-full justify-start">
            <span className="mr-sm">➕</span>
            New Requirement
          </Button>
          <Button variant="secondary" className="w-full justify-start">
            <span className="mr-sm">📊</span>
            View Analytics
          </Button>
          <Button variant="secondary" className="w-full justify-start">
            <span className="mr-sm">⚙️</span>
            Configure Agents
          </Button>
        </div>
      </section>
    </aside>
  );
}

interface AgentCardProps {
  agent: Agent;
  isActive: boolean;
  onClick: () => void;
}

function AgentCard({ agent, isActive, onClick }: AgentCardProps) {
  const agentColors: Record<Agent["type"], string> = {
    finalize: "bg-agent-finalize",
    design: "bg-agent-design",
    code: "bg-agent-code",
    test: "bg-agent-test",
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        "relative p-md rounded-md border cursor-pointer transition-all duration-fast",
        "hover:bg-bg-elevated hover:border-border-secondary hover:translate-x-1",
        isActive
          ? "bg-bg-elevated border-accent-primary"
          : "bg-bg-tertiary border-border-primary",
      )}
    >
      {isActive && (
        <span
          className="absolute left-0 top-1 bottom-1 w-[3px] rounded-full bg-accent-primary"
          aria-hidden="true"
        />
      )}

      <div className="flex items-center gap-sm">
        <div
          className={cn(
            "w-6 h-6 rounded flex items-center justify-center text-sm",
            agentColors[agent.type],
          )}
        >
          {agent.icon}
        </div>

        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-text-primary truncate">
            {agent.name}
          </div>
          <div className="text-xs text-text-tertiary">{agent.statusLabel}</div>
        </div>
      </div>
    </div>
  );
}
