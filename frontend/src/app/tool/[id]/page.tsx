import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Header } from "@/components/header/Header";
import { ToolRunner } from "@/components/tool-runner/ToolRunner";
import { CodeReviewRunner } from "@/components/tool-runner/CodeReviewRunner";
import { getTool } from "@/lib/api/tools";
import { TOOL_BADGE_COLORS } from "@/lib/constants";

export default async function ToolPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const tool = await getTool(id);

  return (
    <div className="min-h-screen bg-zinc-950">
      <Header />

      <main className="mx-auto max-w-3xl px-6 py-16">
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-white"
        >
          ← Back to catalog
        </Link>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-8">
          <Badge
            variant="outline"
            className={TOOL_BADGE_COLORS[tool.tool_type]}
          >
            {tool.tool_type}
          </Badge>

          <h1 className="mt-4 text-3xl font-bold text-white">{tool.name}</h1>

          <p className="mt-4 text-zinc-400">{tool.description}</p>

          <div className="mt-6 flex items-center gap-2 text-sm text-zinc-500">
            ⚡ <span>~{tool.credit_cost_base.toLocaleString()} credits per run</span>
            <span className="relative group">
              <span className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-zinc-600 text-[10px] text-zinc-500 group-hover:border-zinc-400 group-hover:text-zinc-300 transition-colors cursor-default">?</span>
              <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-2 text-xs text-zinc-300 opacity-0 group-hover:opacity-100 transition-opacity duration-150 shadow-lg">
                Estimated cost. Minimum balance to start: {tool.credit_cost_base.toLocaleString()} credits. Actual cost depends on query complexity.
              </span>
            </span>
          </div>

          {tool.tool_type === "research_agent" ? (
            <ToolRunner toolId={tool.id} creditCost={tool.credit_cost_base} />
          ) : tool.tool_type === "code_review" ? (
            <CodeReviewRunner toolId={tool.id} creditCost={tool.credit_cost_base} />
          ) : (
            <Button
              disabled
              className="mt-8 w-full cursor-not-allowed bg-zinc-800 text-zinc-500"
            >
              Runner coming soon
            </Button>
          )}
        </div>
      </main>
    </div>
  );
}
