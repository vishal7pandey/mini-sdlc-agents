export type AgentType = "finalize" | "design" | "code" | "test";

export type AgentStatus = "production" | "coming_soon" | "error";

export interface Agent {
  id: string;
  type: AgentType;
  name: string;
  icon: string;
  status: AgentStatus;
  statusLabel: string;
}

export const AGENTS: Agent[] = [
  {
    id: "finalize",
    type: "finalize",
    name: "Requirements Finalizer",
    icon: "🎯",
    status: "production",
    statusLabel: "Production Ready",
  },
  {
    id: "design",
    type: "design",
    name: "Design Generator",
    icon: "🎨",
    status: "coming_soon",
    statusLabel: "Coming Soon",
  },
  {
    id: "code",
    type: "code",
    name: "Code Generator",
    icon: "⚡",
    status: "coming_soon",
    statusLabel: "Coming Soon",
  },
  {
    id: "test",
    type: "test",
    name: "Test Generator",
    icon: "🧪",
    status: "coming_soon",
    statusLabel: "Coming Soon",
  },
];
