"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useState, useEffect, use } from "react";
import { Search as SearchIcon, X, ChevronDown, ChevronUp, FileText, Database, Gavel, History, Ruler } from "lucide-react";
import Link from "next/link";
import QueryError from "@/components/query-error";

export default function SearchPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  // Debounce the query input (300ms)
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(handler);
  }, [query]);

  const { data: searchRes, isFetching, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["project", projectId, "search", debouncedQuery],
    queryFn: () => api.searchProject(projectId, debouncedQuery),
    enabled: debouncedQuery.length > 0,
  });

  if (isError) return <QueryError message={(error as Error)?.message} retry={refetch} />;

  const rawResults = searchRes?.data || searchRes || [];
  
  // Group by table_name (Entities, Decisions, Conventions, Activity, Documents)
  const groupedResults = Array.isArray(rawResults) ? rawResults.reduce((acc: any, result: any) => {
    const table = result.table_name || "Unknown";
    if (!acc[table]) acc[table] = [];
    acc[table].push(result);
    return acc;
  }, {}) : {};

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const getTableIcon = (tableName: string) => {
    switch (tableName.toLowerCase()) {
      case "entities": return <Database className="w-4 h-4 text-primary" />;
      case "decisions": return <Gavel className="w-4 h-4 text-tertiary" />;
      case "conventions": return <Ruler className="w-4 h-4 text-secondary" />;
      case "activity": return <History className="w-4 h-4 text-on-surface-variant" />;
      case "documents": return <FileText className="w-4 h-4 text-primary-container" />;
      default: return <FileText className="w-4 h-4 text-outline" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
      
      {/* Search Header Area */}
      <div className="mt-8 space-y-6">
        <h1 className="text-4xl font-extrabold tracking-tighter text-on-surface">Global Search</h1>
        <p className="text-on-surface-variant">Find entities, documents, architectural choices, and team conventions.</p>
        
        <div className="relative group">
          <SearchIcon className={`absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 transition-colors ${query ? 'text-primary' : 'text-on-surface-variant group-focus-within:text-primary'}`} />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type to search the semantic graph..."
            className="w-full pl-14 pr-12 py-5 bg-surface-container-low border-2 border-outline-variant/20 rounded-2xl text-lg text-on-surface placeholder:text-outline-variant focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all shadow-sm"
          />
          {query && (
            <button 
              onClick={() => setQuery("")}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-1.5 rounded-full hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Results Container */}
      <div className="space-y-8 mt-8">
        {!debouncedQuery ? (
          <div className="flex flex-col items-center justify-center p-16 text-center border-2 border-dashed border-outline-variant/10 rounded-2xl bg-surface-container-lowest/50">
            <div className="w-16 h-16 rounded-full bg-surface-container-low flex items-center justify-center mb-4">
               <SearchIcon className="w-8 h-8 text-on-surface-variant/50" />
            </div>
            <h3 className="text-lg font-bold text-on-surface">Ready to Search</h3>
            <p className="text-sm text-on-surface-variant mt-1 max-w-sm">Hit the exact entity name or query the codebase concepts for deeper knowledge discovery.</p>
          </div>
        ) : isFetching ? (
          <div className="space-y-6">
            <div className="flex items-center gap-3">
               <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
               <span className="text-sm text-on-surface-variant font-medium">Scanning index...</span>
            </div>
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="p-6 bg-surface-container-low rounded-xl border border-outline-variant/10 animate-pulse space-y-4">
                <div className="h-5 w-48 bg-surface-container-high rounded" />
                <div className="h-4 w-full bg-surface-container rounded" />
                <div className="h-4 w-3/4 bg-surface-container rounded" />
              </div>
            ))}
          </div>
        ) : Object.keys(groupedResults).length === 0 ? (
          <div className="flex flex-col items-center justify-center p-16 text-center bg-surface-container-low rounded-2xl border border-outline-variant/10">
            <span className="material-symbols-outlined text-5xl text-outline-variant mb-4">search_off</span>
            <h3 className="text-lg font-bold text-on-surface">No results found</h3>
            <p className="text-sm text-on-surface-variant mt-1">We couldn't find anything matching "{debouncedQuery}". Try refining your terms.</p>
          </div>
        ) : (
          <div className="space-y-10">
            {Object.keys(groupedResults).sort().map((table) => {
              const tableResults = groupedResults[table];
              const isEntityTable = table.toLowerCase() === "entities";

              return (
                <div key={table} className="space-y-4 animate-in slide-in-from-bottom-2 duration-300">
                  <div className="flex items-center gap-3 pb-2 border-b border-outline-variant/10">
                    {getTableIcon(table)}
                    <h2 className="text-lg font-bold text-on-surface capitalize tracking-tight">{table}</h2>
                    <span className="px-2 py-0.5 rounded-full bg-surface-container-high text-xs font-bold text-on-surface-variant">
                      {tableResults.length}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    {tableResults.map((res: any, idx: number) => {
                      const id = res.id || res.name || `${table}-${idx}`;
                      const isExpanded = expandedItems[id];
                      // The API often returns distance for vector similarity, convert to pseudo relevance %
                      const relevanceScore = res.score ? Math.min(Math.round(res.score * 100), 100) : (res.distance ? Math.max(0, 100 - Math.round((res.distance) * 50)) : 85);

                      return (
                        <div key={id} className="group bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden hover:border-outline-variant/30 transition-all">
                          <div 
                            className={`p-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4 cursor-pointer ${isEntityTable ? 'hover:bg-surface-container-high/30' : ''}`}
                            onClick={() => {
                              if (isEntityTable) {
                                router.push(`/projects/${projectId}/entities/${encodeURIComponent(res.name || res.id)}`);
                              } else {
                                toggleExpand(id);
                              }
                            }}
                          >
                            <div className="flex-1 min-w-0 space-y-1.5">
                              <div className="flex items-start justify-between gap-2">
                                <h3 className="text-base font-bold text-on-surface truncate group-hover:text-primary transition-colors">
                                  {res.title || res.name || res.summary || "Untitled"}
                                </h3>
                                {/* Relevance Score Bar */}
                                <div className="flex items-center gap-2 shrink-0">
                                   <div className="w-16 h-1.5 bg-surface-container-highest rounded-full overflow-hidden hidden sm:block">
                                      <div className="h-full bg-tertiary" style={{ width: `${relevanceScore}%` }} />
                                   </div>
                                   <span className="text-[10px] font-bold text-on-surface-variant">{relevanceScore}%</span>
                                </div>
                              </div>
                              
                              <p className={`text-sm text-on-surface-variant leading-relaxed ${!isExpanded ? 'line-clamp-2' : ''}`}>
                                {res.snippet || res.content || res.body || "No preview available."}
                              </p>

                              {/* Metadata Badges */}
                              <div className="flex flex-wrap items-center gap-2 pt-2">
                                {res.kind && (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest bg-primary/10 text-primary border border-primary/20">
                                    {res.kind}
                                  </span>
                                )}
                                {res.source && (
                                  <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold text-on-surface-variant bg-surface-container border border-outline-variant/10">
                                    {res.source}
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {/* Expand/Navigate hint */}
                            <div className="shrink-0 pt-1 hidden sm:block">
                              {isEntityTable ? (
                                <span className="material-symbols-outlined text-outline-variant group-hover:text-primary transition-colors">arrow_forward</span>
                              ) : (
                                <button className="p-1 rounded-full hover:bg-surface-container-high transition-colors text-on-surface-variant">
                                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </button>
                              )}
                            </div>
                          </div>
                          
                          {/* Expanded Full Content Inline */}
                          {(!isEntityTable && isExpanded) && (
                            <div className="px-5 pb-5 pt-3 border-t border-outline-variant/10 bg-surface-container-lowest/30">
                              <div className="text-sm text-on-surface whitespace-pre-wrap font-mono relative">
                                {res.content || res.body || res.snippet}
                              </div>
                              {/* If it's an activity or decision, maybe provide a subtle link */}
                              <div className="mt-4 flex justify-end">
                                 <button className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
                                    View full context <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                                 </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
