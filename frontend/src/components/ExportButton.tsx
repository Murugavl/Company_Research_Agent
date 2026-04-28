import { Button } from "@/components/ui";
import { Download } from "lucide-react";
import type { AccountPlan } from "@/lib/types";
import { exportToPDF } from "@/lib/export";

interface ExportButtonProps {
  plan: AccountPlan | null;
  companyName: string;
}

export function ExportButton({ plan, companyName }: ExportButtonProps) {
  if (!plan) return null;

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => exportToPDF(plan, companyName)}
      className="text-primary/60 dark:text-white/40 hover:text-primary dark:hover:text-white transition-all font-bold tracking-widest text-[10px] uppercase border border-primary/10 dark:border-white/5 px-4 py-2 rounded-xl bg-primary/5 dark:bg-transparent"
    >
      <Download className="w-3.5 h-3.5 mr-2" />
      Export PDF
    </Button>
  );
}
