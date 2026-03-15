import { ToolType } from "@/lib/api/types";

export const TOOL_BADGE_COLORS: Record<ToolType, string> = {
  research_agent: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  code_review: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  doc_qa: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  resume: "bg-orange-500/20 text-orange-300 border-orange-500/30",
};

export const TOOL_LABELS: Record<ToolType, string> = {
  research_agent: "Research Agent",
  code_review: "Code Review",
  doc_qa: "Document Q&A",
  resume: "Resume",
};
