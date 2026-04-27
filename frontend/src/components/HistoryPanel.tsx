import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { X, Clock, History as HistoryIcon } from "lucide-react";
import { getHistory } from "@/lib/api";
import { formatRelativeTime, cn } from "@/lib/utils";

interface HistoryPanelProps {
  companyName: string;
  sessionId: string;
  onClose: () => void;
}

export function HistoryPanel({ companyName, sessionId, onClose }: HistoryPanelProps) {
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!companyName) return;
    
    let mounted = true;
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const data = await getHistory(companyName, sessionId);
        if (mounted) setHistory(data);
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    fetchHistory();
    
    return () => {
      mounted = false;
    };
  }, [companyName, sessionId]);

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25 }}
      className="fixed inset-y-0 right-0 w-[380px] bg-black/80 backdrop-blur-2xl border-l border-white/10 z-50 flex flex-col shadow-2xl"
    >
      <div className="flex items-center justify-between p-6 border-b border-white/10">
        <h2 className="text-lg font-black tracking-tight flex items-center gap-2">
          <HistoryIcon className="w-5 h-5 text-primary" />
          Research Timeline
        </h2>
        <button 
          onClick={onClose}
          className="p-2 text-white/40 hover:text-white rounded-full hover:bg-white/5 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {!companyName ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
            <HistoryIcon className="w-12 h-12 text-white/20" />
            <p className="text-sm font-medium">Research a company first</p>
          </div>
        ) : isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-white/5 rounded-2xl p-5 space-y-3">
              <div className="w-20 h-3 bg-white/10 rounded" />
              <div className="w-full h-4 bg-white/10 rounded" />
              <div className="w-2/3 h-4 bg-white/10 rounded" />
            </div>
          ))
        ) : history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
            <Clock className="w-12 h-12 text-white/20" />
            <p className="text-sm font-medium">No history yet for this session</p>
          </div>
        ) : (
          history.map((entry, i) => (
            <div 
              key={i} 
              className="bg-white/[0.02] border border-white/5 border-l-2 border-l-primary rounded-2xl p-5 hover:bg-white/[0.05] transition-colors"
            >
              <div className="text-[10px] uppercase tracking-widest text-primary mb-2 font-bold">
                {formatRelativeTime(entry.researched_at || new Date().toISOString())}
              </div>
              <h3 className="font-bold text-white mb-2">{entry.company_name}</h3>
              <p className="text-xs text-white/60 line-clamp-3 leading-relaxed">
                {entry.overview}
              </p>
            </div>
          ))
        )}
      </div>
    </motion.div>
  );
}
