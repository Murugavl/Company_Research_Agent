import { AnimatePresence } from "framer-motion";
import { Toast } from "./Toast";
import type { ToastData } from "@/hooks/useToast";

interface ToastContainerProps {
  toasts: ToastData[];
  removeToast: (id: string) => void;
}

export function ToastContainer({ toasts, removeToast }: ToastContainerProps) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            id={toast.id}
            type={toast.type}
            message={toast.message}
            onRemove={removeToast}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
