import { PageLayout } from "@/components/layout/page-layout";
import { Button } from "@/components/ui/button";

export default function RequirementsPage() {
  return (
    <PageLayout
      title="Process New Requirements"
      subtitle="Send raw user input through the requirements finalization pipeline."
      actions={
        <Button variant="primary">
          <span className="mr-sm">▶️</span>
          Run Agent Pipeline
        </Button>
      }
    >
      <p className="text-base text-text-secondary">
        Requirements processing UI will be implemented in Phase 2.
      </p>
    </PageLayout>
  );
}
