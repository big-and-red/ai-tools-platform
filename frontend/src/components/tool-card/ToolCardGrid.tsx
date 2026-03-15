"use client";

import { useAuth } from "@/components/auth/useAuth";
import { ToolCard } from "./ToolCard";
import type { ToolRead } from "@/lib/api/types";

interface ToolCardGridProps {
  tools: ToolRead[];
}

export function ToolCardGrid({ tools }: ToolCardGridProps) {
  const { user, credits } = useAuth();

  // Block running tools only if user is logged in AND has confirmed negative balance
  const isBlocked = user !== null && credits !== null && credits < 0;

  return (
    <>
      {isBlocked && (
        <div className="mb-8 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Your credit balance is negative (⚡ {credits}). Top up to run new tools.
        </div>
      )}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {tools.map((tool) => (
          <ToolCard key={tool.id} tool={tool} disabled={isBlocked} />
        ))}
      </div>
    </>
  );
}
