"use client";

import { useAuth } from "@/components/auth/useAuth";
import { ToolCard } from "./ToolCard";
import type { ToolRead, ToolType } from "@/lib/api/types";

const TOOL_ORDER: ToolType[] = ["research_agent", "code_review", "doc_qa", "resume"];
const IMPLEMENTED_TOOLS: Set<ToolType> = new Set(["research_agent", "code_review"]);

interface ToolCardGridProps {
  tools: ToolRead[];
}

export function ToolCardGrid({ tools }: ToolCardGridProps) {
  const { user, credits } = useAuth();

  const isBlocked = user !== null && credits !== null && credits < 0;

  const sorted = [...tools].sort(
    (a, b) => TOOL_ORDER.indexOf(a.tool_type) - TOOL_ORDER.indexOf(b.tool_type),
  );

  return (
    <>
      {isBlocked && (
        <div className="mb-8 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Your credit balance is negative (⚡ {credits}). Top up to run new tools.
        </div>
      )}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {sorted.map((tool) => (
          <ToolCard
            key={tool.id}
            tool={tool}
            disabled={isBlocked}
            comingSoon={!IMPLEMENTED_TOOLS.has(tool.tool_type)}
          />
        ))}
      </div>
    </>
  );
}
