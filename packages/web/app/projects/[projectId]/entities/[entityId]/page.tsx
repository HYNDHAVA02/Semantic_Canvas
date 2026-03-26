"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import Link from "next/link";
import { use, useState } from "react";
import { ArrowLeft, Box, LayoutGrid, Layers, Hexagon, Activity } from "lucide-react";

export default function EntityDetailPage(props: { params: Promise<{ projectId: string; entityId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const entityId = params.entityId;

  // Run blast radius explicitly when triggered
  const [showBlastRadius, setShowBlastRadius] = useState(false);

  const { data: entityRes, isLoading: entityLoading } = useQuery({
    queryKey: ["project", projectId, "entity", entityId],
    queryFn: () => api.getProjectEntity(projectId, entityId),
  });

  const { data: relsRes, isLoading: relsLoading } = useQuery({
    queryKey: ["project", projectId, "relationships", entityId],
    queryFn: () => api.getRelationships(projectId, entityId),
  });

  const { data: activityRes, isLoading: actLoading } = useQuery({
    queryKey: ["project", projectId, "activity"],
    queryFn: () => api.getProjectActivity(projectId, 10),
  });

  const { data: blastRadiusRes, isLoading: blastLoading } = useQuery({
    queryKey: ["project", projectId, "blast-radius", entityId],
    queryFn: () => api.getBlastRadius(projectId, entityId, 3),
    enabled: showBlastRadius,
  });

  const entity = entityRes?.data || entityRes || {}; // Fallbacks based on API shape
  const relationships = relsRes?.data || relsRes || [];
  const activities = activityRes?.data || activityRes || [];
  
  // Try to accurately separate incoming vs outgoing based on from_entity_id == entityId vs to_entity_id
  const outgoing = relationships.filter((r: any) => r.from_entity_id === entityId || r.from_entity_id === entity.id || r.from_entity_name === entity.name);
  const incoming = relationships.filter((r: any) => r.to_entity_id === entityId || r.to_entity_id === entity.id || r.to_entity_name === entity.name);

  const renderRelationships = (rels: any[], title: string, direction: "in" | "out") => (
    <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 flex-1">
      <h3 className="text-sm font-bold tracking-widest uppercase text-on-surface-variant mb-4 flex items-center gap-2">
         {direction === "out" ? <span className="material-symbols-outlined text-primary text-sm">logout</span> : <span className="material-symbols-outlined text-secondary text-sm">login</span>}
         {title} ({rels.length})
      </h3>
      {rels.length > 0 ? (
        <ul className="space-y-3">
          {rels.map((rel, idx) => {
            // display correct corresponding entity based on direction
            const connectionName = direction === "out" ? (rel.to_entity_name || rel.to_entity_id) : (rel.from_entity_name || rel.from_entity_id);
            return (
              <li key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-surface-container border border-outline-variant/5">
                 <Link href={`/projects/${projectId}/entities/${encodeURIComponent(connectionName)}`} className="text-sm font-medium text-on-surface hover:text-primary transition-colors">
                    {connectionName}
                 </Link>
                 <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 mt-2 sm:mt-0 rounded-md bg-surface-container-highest text-on-surface-variant border border-outline-variant/10">
                   {rel.kind || "Connects"}
                 </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-xs text-on-surface-variant italic py-4">No {title.toLowerCase()} found.</p>
      )}
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
      {/* Back Link */}
      <Link href={`/projects/${projectId}/entities`} className="inline-flex items-center gap-2 text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Entities
      </Link>

      {/* Entity Metadata Header */}
      {entityLoading ? (
         <div className="p-8 bg-surface-container-low rounded-xl border border-outline-variant/10 animate-pulse space-y-4">
            <div className="h-10 w-64 bg-surface-container-high rounded" />
            <div className="h-4 w-48 bg-surface-container rounded" />
         </div>
      ) : (
        <div className="p-8 bg-surface-container-low rounded-xl border border-outline-variant/10 flex flex-col md:flex-row md:items-start justify-between gap-6 relative overflow-hidden">
          {/* subtle accent background */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-3xl -z-10 rounded-full mix-blend-screen pointer-events-none" />
          
          <div className="space-y-4 z-10 flex-1">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-surface-container-high border border-outline-variant/20 flex items-center justify-center shrink-0 shadow-sm text-primary">
                <Box className="w-6 h-6" />
              </div>
              <div>
                 <h1 className="text-3xl font-bold tracking-tight text-on-surface break-words">{entity.name || decodeURIComponent(entityId)}</h1>
                 <p className="text-sm text-on-surface-variant flex items-center gap-2 mt-1">
                   {entity.source || "System Extracted"} &bull; Last seen: {entity.updated_at ? new Date(entity.updated_at).toLocaleDateString() : (entity.last_seen || "Just now")}
                 </p>
              </div>
            </div>
            
            <div className="flex flex-wrap items-center gap-2 pt-2">
               <span className="px-3 py-1 rounded-md text-[10px] font-bold uppercase tracking-widest border bg-primary/10 text-primary border-primary/20">
                  {entity.kind || "Unknown"}
               </span>
               <span className="px-3 py-1 text-xs font-medium bg-surface-container rounded-md border border-outline-variant/10 text-on-surface-variant">
                 ID: {entity.id || entityId}
               </span>
            </div>
          </div>

          <div className="p-4 bg-surface-container rounded-lg border border-outline-variant/10 text-sm space-y-2 min-w-48 z-10">
            <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-3">Metadata</p>
            {entity.metadata && Object.keys(entity.metadata).length > 0 ? (
               Object.entries(entity.metadata).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-outline-variant/5 pb-1 last:border-0 last:pb-0">
                  <span className="text-on-surface-variant">{k}</span>
                  <span className="font-medium text-on-surface max-w-[200px] truncate text-right">{String(v)}</span>
                </div>
               ))
            ) : (
               <p className="text-xs text-on-surface-variant italic">No metadata available</p>
            )}
          </div>
        </div>
      )}

      {/* Relationships Grid */}
      <div className="flex flex-col md:flex-row gap-6">
        {renderRelationships(incoming, "Incoming dependencies", "in")}
        {renderRelationships(outgoing, "Outgoing dependencies", "out")}
      </div>

      {/* Blast Radius Section */}
      <div className="p-6 md:p-8 bg-surface-container-low rounded-xl border border-outline-variant/10 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-outline-variant/10 pb-6">
           <div className="flex items-center gap-3">
             <div className="p-2 rounded-lg bg-tertiary/10 text-tertiary">
               <Hexagon className="w-5 h-5" />
             </div>
             <div>
               <h2 className="text-lg font-bold text-on-surface">Blast Radius Analysis</h2>
               <p className="text-xs text-on-surface-variant">Calculate propagation depth of potential changes.</p>
             </div>
           </div>
           <button 
             onClick={() => setShowBlastRadius(true)}
             disabled={blastLoading}
             className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container disabled:opacity-50 transition-colors shadow-sm"
           >
             {blastLoading ? "Analyzing..." : "Run Analysis (Depth: 3)"}
           </button>
        </div>

        {showBlastRadius && (
          <div className="pt-2">
            {blastLoading ? (
               <div className="h-32 flex items-center justify-center text-on-surface-variant">
                 <div className="flex items-center gap-2 animate-pulse">
                   <div className="w-2 h-2 rounded-full bg-tertiary" />
                   <div className="w-2 h-2 rounded-full bg-tertiary animation-delay-200" />
                   <div className="w-2 h-2 rounded-full bg-tertiary animation-delay-400" />
                 </div>
               </div>
            ) : blastRadiusRes ? (() => {
              // API returns { forward: [...], reverse: [...] } with depth on each node
              const allNodes = [
                ...(blastRadiusRes.forward || []),
                ...(blastRadiusRes.reverse || []),
              ];
              // Deduplicate by id, keeping the entry with smallest depth
              const seen = new Map<string, any>();
              for (const n of allNodes) {
                const key = n.id || n.name;
                if (!seen.has(key) || n.depth < seen.get(key).depth) {
                  seen.set(key, n);
                }
              }
              const uniqueNodes = Array.from(seen.values());
              const maxDepth = uniqueNodes.length > 0
                ? Math.max(...uniqueNodes.map((n: any) => n.depth || 1))
                : 0;

              if (uniqueNodes.length === 0) {
                return (
                  <div className="text-sm text-on-surface-variant p-4 text-center">
                    No impact detected — this entity has no relationships.
                  </div>
                );
              }

              return (
                <div className="space-y-8 animate-in slide-in-from-bottom-2 duration-300">
                  <div className="flex gap-6 text-sm text-on-surface-variant mb-2">
                    <span>Forward impact: <strong className="text-on-surface">{(blastRadiusRes.forward || []).length}</strong></span>
                    <span>Reverse impact: <strong className="text-on-surface">{(blastRadiusRes.reverse || []).length}</strong></span>
                    <span>Total unique: <strong className="text-on-surface">{uniqueNodes.length}</strong></span>
                  </div>
                  {Array.from({ length: maxDepth }).map((_, depthIndex) => {
                    const depth = depthIndex + 1;
                    const nodesAtDepth = uniqueNodes.filter((n: any) => n.depth === depth);

                    if (nodesAtDepth.length === 0) return null;

                    return (
                      <div key={depth} className="relative">
                        {depth > 1 && (
                          <div className="absolute -top-6 left-6 w-0.5 h-6 bg-outline-variant/30" />
                        )}
                        <div className="flex items-center gap-3 mb-4">
                          <span className="w-6 h-6 rounded-full bg-surface-container-highest border border-outline-variant/20 flex items-center justify-center text-xs font-bold text-on-surface-variant shadow-sm z-10">
                            {depth}
                          </span>
                          <h4 className="text-sm font-bold text-on-surface">Degree {depth} Impact ({nodesAtDepth.length})</h4>
                        </div>
                        <div className="ml-3 pl-6 border-l-2 border-outline-variant/10 gap-2 flex flex-wrap">
                          {nodesAtDepth.map((n: any, idx: number) => (
                            <Link key={idx} href={`/projects/${projectId}/entities/${n.id || n.name}`} className="px-3 py-1.5 bg-surface-container rounded-md border border-outline-variant/10 text-xs font-medium hover:bg-surface-container-highest transition-colors flex items-center gap-2">
                              <Layers className="w-3 h-3 text-tertiary" />
                              {n.name || n.id}
                            </Link>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })() : (
               <div className="text-sm text-on-surface-variant p-4 text-center">Failed to load analysis graph results.</div>
            )}
          </div>
        )}
      </div>

      {/* Recent Activity Section */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold tracking-tight text-on-surface flex items-center gap-2 px-2">
           <Activity className="w-5 h-5 text-primary" />
           Project Activity
        </h3>
        <div className="bg-surface-container-lowest rounded-xl border border-outline-variant/10 overflow-hidden">
          {activities.length > 0 ? (
             <div className="divide-y divide-outline-variant/10">
               {activities.map((act: any, idx: number) => {
                  let icon = "terminal";
                  let iconColor = "text-primary";
                  if(act.source === "Agent" || act.source === "ai") {
                    icon = "smart_toy";
                    iconColor = "text-tertiary";
                  } else if (act.source === "Manual" || act.source === "user") {
                    icon = "edit_note";
                    iconColor = "text-secondary";
                  }

                  return (
                    <div key={act.id || idx} className="p-4 flex items-center gap-4 hover:bg-surface-container-low transition-colors group cursor-pointer">
                      <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0">
                        <span className={`material-symbols-outlined text-lg ${iconColor}`}>{icon}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="font-semibold text-on-surface truncate">{act.summary}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-container-highest text-on-surface-variant uppercase tracking-tighter">
                            {act.source || "System"}
                          </span>
                        </div>
                        <p className="text-xs text-on-surface-variant">Authored by <span className="text-on-surface">{act.actor || "System"}</span></p>
                      </div>
                      <span className="material-symbols-outlined opacity-0 group-hover:opacity-100 transition-opacity text-on-surface-variant">arrow_forward_ios</span>
                    </div>
                  )
               })}
             </div>
          ) : (
             <div className="p-8 flex flex-col items-center justify-center text-center">
               <span className="material-symbols-outlined text-4xl text-outline-variant mb-2">history_toggle_off</span>
               <p className="text-sm text-on-surface-variant">No related activity.</p>
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
