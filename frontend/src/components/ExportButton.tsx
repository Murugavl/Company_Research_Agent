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
      className="text-white/40 hover:text-white transition-all font-bold tracking-widest text-[10px] uppercase"
    >
      <Download className="w-3.5 h-3.5 mr-2" />
      Export PDF
    </Button>
  );
}
