import { cn } from "@/lib/utils";

export function PlanSkeleton() {
  const renderCard = (key: string, isFullWidth = false) => (
    <div
      key={key}
      className={cn(
        "h-full rounded-3xl border border-white/5 bg-white/[0.03] p-6 flex flex-col gap-6",
        isFullWidth ? "md:col-span-2" : ""
      )}
    >
      <div className="flex items-center gap-4">
        <div className="w-11 h-11 rounded-2xl bg-white/5 animate-pulse" />
        <div className="w-32 h-4 rounded bg-white/5 animate-pulse" />
      </div>
      <div className="space-y-3 flex-1">
        <div className="w-full h-3 rounded bg-white/5 animate-pulse" />
        <div className="w-5/6 h-3 rounded bg-white/5 animate-pulse" />
        <div className="w-4/5 h-3 rounded bg-white/5 animate-pulse" />
        {!isFullWidth && <div className="w-2/3 h-3 rounded bg-white/5 animate-pulse" />}
      </div>
    </div>
  );

  return (
    <div className="space-y-12 pb-24">
      {/* Header Skeleton */}
      <div className="flex items-end justify-between gap-8 border-b border-white/5 pb-10">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-16 h-6 rounded-full bg-white/5 animate-pulse" />
            <div className="w-32 h-3 rounded bg-white/5 animate-pulse" />
          </div>
          <div className="w-64 h-12 rounded bg-white/5 animate-pulse" />
        </div>
        <div className="flex flex-col items-end gap-2 text-right">
          <div className="w-24 h-3 rounded bg-white/5 animate-pulse" />
          <div className="w-16 h-3 rounded bg-white/5 animate-pulse" />
        </div>
      </div>

      {/* Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {renderCard("skel-overview", true)}
        {Array.from({ length: 8 }).map((_, i) => renderCard(`skel-${i}`))}
      </div>
    </div>
  );
}
