export type ToolType =
  | "research_agent"
  | "code_review"
  | "doc_qa"
  | "resume";

export interface ToolRead {
  id: string;
  name: string;
  description: string;
  tool_type: ToolType;
  credit_cost_base: number;
  is_active: boolean;
}
