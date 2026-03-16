import Link from "next/link";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TOOL_BADGE_COLORS, TOOL_LABELS } from "@/lib/constants";
import { ToolCardProps } from "./ToolCard.types";

export function ToolCard({ tool, disabled = false, comingSoon = false }: ToolCardProps) {
  const dimmed = disabled || comingSoon;

  return (
    <Card
      className={`relative flex flex-col bg-zinc-900 border-zinc-800 transition-colors duration-200 ${
        dimmed ? "opacity-50 grayscale-[30%]" : "hover:border-violet-500/50"
      }`}
    >
      {comingSoon && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl">
          <span className="rounded-full border border-zinc-600 bg-zinc-900/90 px-4 py-1.5 text-xs font-medium tracking-wide text-zinc-300 uppercase">
            Coming Soon
          </span>
        </div>
      )}
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <Badge
            variant="outline"
            className={TOOL_BADGE_COLORS[tool.tool_type]}
          >
            {TOOL_LABELS[tool.tool_type]}
          </Badge>
          <span className="text-xs text-zinc-500">
            ⚡ {tool.credit_cost_base.toLocaleString("ru-RU")} credits
          </span>
        </div>
        <h2 className="text-lg font-semibold text-white mt-2">{tool.name}</h2>
      </CardHeader>

      <CardContent className="flex-1">
        <p className="text-sm text-zinc-400 line-clamp-3">{tool.description}</p>
      </CardContent>

      <CardFooter>
        {dimmed ? (
          <span className="inline-flex w-full cursor-not-allowed items-center justify-center rounded-md bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-500">
            {comingSoon ? "Coming Soon" : "No credits"}
          </span>
        ) : (
          <Link
            href={`/tool/${tool.id}`}
            className="inline-flex w-full items-center justify-center rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500"
          >
            Run →
          </Link>
        )}
      </CardFooter>
    </Card>
  );
}
