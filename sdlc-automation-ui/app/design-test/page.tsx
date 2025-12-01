export default function DesignTest() {
  return (
    <main className="p-lg space-y-md">
      <section>
        <h1 className="text-display font-semibold mb-md">Design System Test</h1>
        <p className="text-sm text-text-secondary">
          Typography, colors, spacing, and scrollbars powered by Tailwind tokens.
        </p>
      </section>

      <section className="space-y-sm">
        <h2 className="text-lg font-medium">Agent Colors</h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-md">
          <div className="bg-agent-finalize p-md rounded-lg shadow-sm">Finalize</div>
          <div className="bg-agent-design p-md rounded-lg shadow-sm">Design</div>
          <div className="bg-agent-code p-md rounded-lg shadow-sm">Code</div>
          <div className="bg-agent-test p-md rounded-lg shadow-sm">Test</div>
        </div>
      </section>
    </main>
  );
}
