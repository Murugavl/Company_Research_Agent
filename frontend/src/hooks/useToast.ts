import { useState, useCallback } from "react";

export interface ToastData {
  id: string;
  type: "error" | "success" | "info";
  message: string;
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const addToast = useCallback(
    ({ type, message }: { type: "error" | "success" | "info"; message: string }) => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, type, message }]);
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return { toasts, addToast, removeToast };
}
