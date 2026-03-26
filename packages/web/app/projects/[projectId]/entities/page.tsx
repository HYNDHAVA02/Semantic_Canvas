"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import Link from "next/link";
import { use, useState } from "react";
import { Search } from "lucide-react";
import QueryError from "@/components/query-error";

export default function EntitiesListPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const [kindFilter, setKindFilter] = useState("All");

  const { data: entitiesRes, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["project", projectId, "entities", 1000],
    queryFn: () => api.getProjectEntities(projectId, 1000),
  });

  if (isError) return <QueryError message={(error as Error)?.message} retry={refetch} />;

  const entities = entitiesRes?.data || [];
  
  const filteredEntities = kindFilter === "All" 
    ? entities 
    : entities.filter((e: any) => e.kind?.toLowerCase() === kindFilter.toLowerCase());

  const filters = ["All", "Service", "Function", "Class", "Module"];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-extrabold tracking-tighter text-on-surface">Entities</h1>
        <p className="text-on-surface-variant max-w-2xl">
          Browse and filter all semantic abstractions extracted from the codebase.
        </p>
      </div>

      {/* Filters & Search Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 p-1 bg-surface-container-low rounded-lg border border-outline-variant/10">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setKindFilter(f)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium tracking-tight transition-colors ${
                kindFilter === f 
                  ? "bg-surface-container-highest text-primary shadow-sm" 
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
          <input 
            type="text" 
            placeholder="Search entities..." 
            className="w-full sm:w-64 pl-9 pr-4 py-2 bg-surface-container-low border border-outline-variant/10 rounded-lg text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition"
          />
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-outline-variant/10 bg-surface-container text-on-surface-variant tracking-widest uppercase text-xs">
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">Kind</th>
                <th className="px-6 py-4 font-medium hidden sm:table-cell">Source</th>
                <th className="px-6 py-4 font-medium text-right">Last Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-4"><div className="h-4 w-48 bg-surface-container-high rounded" /></td>
                    <td className="px-6 py-4"><div className="h-4 w-20 bg-surface-container-high rounded" /></td>
                    <td className="px-6 py-4 hidden sm:table-cell"><div className="h-4 w-24 bg-surface-container-high rounded" /></td>
                    <td className="px-6 py-4 flex justify-end"><div className="h-4 w-20 bg-surface-container-high rounded" /></td>
                  </tr>
                ))
              ) : filteredEntities.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-on-surface-variant">
                    <div className="flex flex-col items-center justify-center gap-2">
                       <span className="material-symbols-outlined text-4xl text-outline-variant">search_off</span>
                       <p>No entities found for "{kindFilter}"</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredEntities.map((entity: any) => {
                  // Some basic defensive checks for mock/API missing data
                  const kindColors: Record<string, string> = {
                    service: "bg-primary/10 text-primary border-primary/20",
                    function: "bg-tertiary/10 text-tertiary border-tertiary/20",
                    class: "bg-secondary/10 text-secondary border-secondary/20",
                  };
                  const lowerKind = (entity.kind || "").toLowerCase();
                  const kindStyle = kindColors[lowerKind] || "bg-outline-variant/10 text-on-surface border-outline-variant/20";
                  
                  return (
                    <tr key={entity.id || entity.name} className="hover:bg-surface-container transition-colors group">
                      <td className="px-6 py-4">
                        <Link 
                           href={`/projects/${projectId}/entities/${entity.id || entity.name}`}
                           className="font-medium text-on-surface hover:text-primary transition-colors flex items-center gap-2"
                        >
                          <span className="material-symbols-outlined text-[16px] text-outline-variant group-hover:text-primary">arrow_right_alt</span>
                          {entity.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-widest border ${kindStyle}`}>
                          {entity.kind || "Unknown"}
                        </span>
                      </td>
                      <td className="px-6 py-4 hidden sm:table-cell text-on-surface-variant">
                        {entity.source || "System"}
                      </td>
                      <td className="px-6 py-4 text-right text-on-surface-variant whitespace-nowrap">
                        {entity.updated_at ? new Date(entity.updated_at).toLocaleDateString() : (entity.last_seen || "Just now")}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
        
        {!isLoading && filteredEntities.length > 0 && (
          <div className="p-4 border-t border-outline-variant/10 flex items-center justify-between text-xs text-on-surface-variant">
            <span>Showing {filteredEntities.length} entities</span>
            <div className="flex items-center gap-2">
              <button className="px-2 py-1 hover:text-on-surface transition">Previous</button>
              <button className="px-2 py-1 hover:text-on-surface transition">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
