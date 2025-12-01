import { PageLayout } from "@/components/layout/page-layout";
import { StatCard } from "@/components/ui/stat-card";

export default function DashboardPage() {
  return (
    <PageLayout
      title="Multi-Agent SDLC Dashboard"
      subtitle="Multi-agent SDLC automation platform"
    >
      <section className="mb-xl">
        <div className="grid gap-lg grid-cols-1 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Requirements finalized"
            value="24"
            change="+12% vs last week"
            icon={"🎯"}
          />
          <StatCard
            label="Avg. turnaround time"
            value="8m"
            change="-18% vs last run"
            icon={"⏱"}
            iconColor="bg-teal/20 text-teal"
          />
          <StatCard
            label="Active agents"
            value="4"
            change="All healthy"
            icon={"🤖"}
            iconColor="bg-agent-code/20 text-agent-code"
          />
          <StatCard
            label="Errors (24h)"
            value="0"
            change="Stable"
            icon={"✅"}
            iconColor="bg-success/20 text-success"
          />
        </div>
      </section>

      <section>
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-xl">
          <h2 className="text-xl font-semibold mb-lg text-text-primary">
            Agent Pipeline Flow
          </h2>
          <p className="text-base text-text-secondary">
            Pipeline visualization will be implemented in Phase 3.
          </p>
        </div>
      </section>
    </PageLayout>
  );
}
