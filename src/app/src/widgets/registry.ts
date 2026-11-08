import type { ComponentType } from "react";

import type { JsonRecord } from "../guards";
import { ExamCalendar } from "./ExamCalendar";
import { FinanceWidget } from "./FinanceWidget";
import { ProgressWidget } from "./ProgressWidget";

export interface WidgetProps {
  output: JsonRecord;
}

export const TOOL_WIDGETS: Record<string, ComponentType<WidgetProps>> = {
  get_curriculum: ProgressWidget,
  get_financial_summary: FinanceWidget,
  list_online_exams: ExamCalendar,
};
