import { useEffect } from "react";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToastProps {
  id: string;
  type: "error" | "success" | "info";
  message: string;
  onRemove: (id: string) => void;
}

export function Toast({ id, type, message, onRemove }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(id);
    }, 4000);
    return () => clearTimeout(timer);
  }, [id, onRemove]);

  const getIcon = () => {
    switch (type) {
      case "error":
        return <AlertCircle className="w-5 h-5 text-rose-400" />;
      case "success":
        return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case "info":
        return <Info className="w-5 h-5 text-blue-400" />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case "error":
        return "bg-rose-500/10 border-rose-500/20";
      case "success":
        return "bg-emerald-500/10 border-emerald-500/20";
      case "info":
        return "bg-blue-500/10 border-blue-500/20";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className={cn(
        "flex items-start gap-3 p-4 rounded-2xl border shadow-2xl backdrop-blur-xl min-w-[300px] max-w-md",
        getStyles()
      )}
    >
      <div className="shrink-0 mt-0.5">{getIcon()}</div>
      <p className="flex-1 text-sm text-white/90">{message}</p>
      <button
        onClick={() => onRemove(id)}
        className="shrink-0 text-white/40 hover:text-white transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
}
