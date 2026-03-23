"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useState, use } from "react";
import { History, Terminal, Bot, User, Cpu } from "lucide-react";

export default function ActivityPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;

  const sources = ["All", "agent", "user", "axon", "github"];
  const [sourceFilter, setSourceFilter] = useState("All");

  // Keep manual page offset state for direct append/refetch manipulation logic commonly seen in linear paginations
  const [offset, setOffset] = useState(0);
  const LIMIT = 20; // bigger batch

  const { data: activityRes, isLoading, isFetching } = useQuery({
    queryKey: ["project", projectId, "activity", offset],
    queryFn: () => api.getProjectActivity(projectId, LIMIT, offset),
  });

  const latestActivities = Array.isArray(activityRes?.data) ? activityRes.data : (Array.isArray(activityRes) ? activityRes : []);
  
  // Note: For a true append buffer in Next15/ReactQuery, using `useInfiniteQuery` is ideal.
  // We mock a local continuous array by manually reducing or relying solely on next pages fetching directly.
  // For simplicity aligned with typical REST lists without strict persistence, we just show the batch.
  const displayedActivities = sourceFilter === "All" 
    ? latestActivities 
    : latestActivities.filter((a: any) => (a.source || "").toLowerCase().includes(sourceFilter.toLowerCase()) || sourceFilter.toLowerCase().includes((a.source || "").toLowerCase()));

  const getSourceIcon = (source: string) => {
    const s = (source || "").toLowerCase();
    if (s.includes("agent") || s.includes("ai")) return <Bot className="w-5 h-5 text-tertiary" />;
    if (s.includes("user") || s.includes("manual")) return <User className="w-5 h-5 text-secondary" />;
    if (s.includes("axon")) return <Cpu className="w-5 h-5 text-primary" />;
    return <Terminal className="w-5 h-5 text-outline-variant" />;
  };

  const getBadgeColor = (source: string) => {
    const s = (source || "").toLowerCase();
    if (s.includes("agent") || s.includes("ai")) return "bg-tertiary/10 text-tertiary border-tertiary/20";
    if (s.includes("user") || s.includes("manual")) return "bg-secondary/10 text-secondary border-secondary/20";
    if (s.includes("axon")) return "bg-primary/10 text-primary border-primary/20";
    return "bg-surface-container border-outline-variant/10 text-on-surface-variant";
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-on-surface">
          <History className="w-6 h-6 text-on-surface-variant" />
          <h1 className="text-4xl font-extrabold tracking-tighter">Activity Log</h1>
        </div>
        <p className="text-on-surface-variant max-w-2xl">
          Complete historical ledger of graph semantic extractions, refactors, and AI inferences.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-center bg-surface-container-low border border-outline-variant/10 rounded-xl p-4 gap-4">
         <span className="text-sm font-bold tracking-widest text-on-surface-variant uppercase">Filter Event Stream</span>
         <div className="flex flex-wrap items-center gap-2">
            {sources.map(s => (
               <button 
                  key={s} 
                  onClick={() => setSourceFilter(s)}
                  className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider border transition-colors ${sourceFilter === s ? 'bg-surface-container-highest border-outline-variant/20 text-on-surface shadow-sm' : 'bg-transparent border-transparent text-on-surface-variant hover:bg-surface-container'}`}
               >
                  {s}
               </button>
            ))}
         </div>
      </div>

      <div className="bg-surface-container-lowest rounded-xl border border-outline-variant/10 overflow-hidden relative">
        {isFetching && offset === 0 && (
           <div className="absolute inset-0 z-10 bg-surface-container-lowest/50 backdrop-blur-sm flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent animate-spin rounded-full" />
           </div>
        )}
        
        {displayedActivities.length === 0 && !isLoading ? (
          <div className="p-16 text-center">
             <Terminal className="w-12 h-12 text-outline-variant mx-auto mb-4" />
             <h3 className="text-lg font-bold text-on-surface">No events found.</h3>
             <p className="text-sm text-on-surface-variant">Stream bounds returned empty for this log segment.</p>
          </div>
        ) : (
          <div className="divide-y divide-outline-variant/5">
             {displayedActivities.map((act: any, idx: number) => (
                <div key={act.id || idx} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-container transition-colors group">
                   <div className="flex items-start gap-4 flex-1">
                      <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0 border border-outline-variant/5">
                         {getSourceIcon(act.source)}
                      </div>
                      <div className="space-y-1">
                         <div className="flex items-center gap-2">
                            <span className="font-bold text-on-surface group-hover:text-primary transition-colors">{act.summary || "System Execution"}</span>
                            <span className={`px-2 py-0.5 rounded text-[9px] uppercase tracking-widest font-bold border ${getBadgeColor(act.source)}`}>{act.source || "System"}</span>
                         </div>
                         <div className="text-xs text-on-surface-variant flex items-center gap-2">
                           <span>Actor: <strong className="text-on-surface">{act.actor || "AI"}</strong></span>
                         </div>
                      </div>
                   </div>
                   <div className="text-xs font-medium text-on-surface-variant shrink-0 self-end sm:self-auto bg-surface-container-low px-2 py-1 rounded border border-outline-variant/5">
                      {act.created_at || act.timestamp ? new Date(act.created_at || act.timestamp).toLocaleString() : "Just now"}
                   </div>
                </div>
             ))}
          </div>
        )}
      </div>

      {displayedActivities.length >= LIMIT && (
        <div className="flex justify-center pt-4">
           <button 
             onClick={() => setOffset(offset + LIMIT)}
             disabled={isFetching}
             className="px-6 py-2.5 rounded-full border border-outline-variant/10 text-sm font-bold text-on-surface hover:bg-surface-container-high transition-colors bg-surface-container-low shadow-sm flex items-center gap-2 disabled:opacity-50"
           >
             {isFetching ? "Loading..." : "Load Older Events"}
             {!isFetching && <History className="w-4 h-4 text-outline" />}
           </button>
        </div>
      )}
    </div>
  );
}
