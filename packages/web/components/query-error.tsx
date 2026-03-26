"use client";

import { AlertTriangle } from "lucide-react";

export default function QueryError({ message, retry }: { message?: string; retry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-error/20 rounded-xl p-12">
      <AlertTriangle className="w-10 h-10 text-error" />
      <h3 className="text-lg font-bold text-on-surface">Failed to load data</h3>
      <p className="text-sm text-on-surface-variant max-w-md text-center">
        {message || "Something went wrong. Please try again."}
      </p>
      {retry && (
        <button
          onClick={retry}
          className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary/80 transition-colors mt-2"
        >
          Retry
        </button>
      )}
    </div>
  );
}
