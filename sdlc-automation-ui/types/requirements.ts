export type RequirementStatus =
  | "ok"
  | "partially_ok"
  | "needs_clarification"
  | "needs_human_review";

export interface RequirementsSummary {
  id: string;
  title: string;
  status: RequirementStatus;
  createdAt: string;
}
