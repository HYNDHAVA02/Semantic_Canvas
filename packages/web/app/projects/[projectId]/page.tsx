"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { use } from "react";

export default function ProjectOverviewPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;

  const { data: project, isLoading: prjLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
  });

  const { data: entities, isLoading: entLoading } = useQuery({
    queryKey: ["project", projectId, "entities"],
    queryFn: () => api.getProjectEntities(projectId),
  });

  const { data: decisions, isLoading: decLoading } = useQuery({
    queryKey: ["project", projectId, "decisions"],
    queryFn: () => api.getProjectDecisions(projectId),
  });

  const { data: activities, isLoading: actLoading } = useQuery({
    queryKey: ["project", projectId, "activity"],
    queryFn: () => api.getProjectActivity(projectId),
  });

  const isLoading = prjLoading || entLoading || actLoading || decLoading;

  // Transform entities dynamically by grouping on "kind"
  const entityGroupCounts = (entities?.data || []).reduce((acc: any, entity: any) => {
    const kind = entity.kind || 'Unknown';
    acc[kind] = (acc[kind] || 0) + 1;
    return acc;
  }, {});
  
  const totalEntities = (entities?.data || []).length;
  // If no entities yet (empty state case)
  const isDataEmpty = !isLoading && totalEntities === 0;

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 animate-pulse">
        <div className="h-12 w-64 bg-surface-container-high rounded" />
        <div className="h-4 w-96 bg-surface-container-low rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
           <div className="h-32 bg-surface-container-low rounded-xl" />
           <div className="h-32 bg-surface-container-low rounded-xl" />
           <div className="h-32 bg-surface-container-low rounded-xl" />
           <div className="h-32 bg-surface-container-low rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Header Section */}
      <section className="mb-12">
        <h2 className="text-4xl font-extrabold tracking-tighter text-on-surface mb-2">Workspace Overview</h2>
        <p className="text-on-surface-variant max-w-2xl">
          Visualizing the semantic architecture of your project. {project?.description || ""}
        </p>
      </section>

      {/* Metric Cards Bento Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {/* Total Entities */}
        <div className="bg-surface-container-low p-6 rounded-xl border border-outline-variant/10 group hover:bg-surface-container transition-all duration-300">
          <div className="flex justify-between items-start mb-4">
            <span className="material-symbols-outlined text-primary p-2 bg-primary/10 rounded-lg">database</span>
            <span className="text-xs font-medium text-primary tracking-widest uppercase">Live</span>
          </div>
          <div className="text-3xl font-bold text-on-surface mb-1">{totalEntities}</div>
          <div className="text-sm text-on-surface-variant font-medium">Total Entities</div>
          <div className="mt-4 h-1 w-full bg-surface-container-highest rounded-full overflow-hidden">
            <div className="h-full bg-primary w-[72%]"></div>
          </div>
        </div>

        {/* Total Relationships Placeholder */}
        <div className="bg-surface-container-low p-6 rounded-xl border border-outline-variant/10 group hover:bg-surface-container transition-all duration-300">
          <div className="flex justify-between items-start mb-4">
            <span className="material-symbols-outlined text-primary p-2 bg-primary/10 rounded-lg">account_tree</span>
            <span className="text-xs font-medium text-on-surface-variant tracking-widest uppercase">Verified</span>
          </div>
          <div className="text-3xl font-bold text-on-surface mb-1">--</div>
          <div className="text-sm text-on-surface-variant font-medium">Total Relationships</div>
          <div className="mt-4 flex gap-1">
            <div className="h-1 flex-1 bg-primary rounded-full"></div>
            <div className="h-1 flex-1 bg-primary rounded-full"></div>
            <div className="h-1 flex-1 bg-surface-container-highest rounded-full"></div>
          </div>
        </div>

        {/* Decisions Logged */}
        <div className="bg-surface-container-low p-6 rounded-xl border border-outline-variant/10 group hover:bg-surface-container transition-all duration-300">
          <div className="flex justify-between items-start mb-4">
            <span className="material-symbols-outlined text-primary p-2 bg-primary/10 rounded-lg">gavel</span>
            <span className="text-xs font-medium text-tertiary tracking-widest uppercase">+ {decisions?.data?.length || 0} New</span>
          </div>
          <div className="text-3xl font-bold text-on-surface mb-1">{decisions?.data?.length || 0}</div>
          <div className="text-sm text-on-surface-variant font-medium">Decisions Logged</div>
          <div className="mt-4 text-xs text-on-surface-variant italic truncate">
            Last: {decisions?.data?.[0]?.title ? `"${decisions.data[0].title}"` : "No decisions yet"}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-surface-container-low p-6 rounded-xl border border-outline-variant/10 group hover:bg-surface-container transition-all duration-300">
          <div className="flex justify-between items-start mb-4">
            <span className="material-symbols-outlined text-primary p-2 bg-primary/10 rounded-lg">history</span>
            <span className="text-xs font-medium text-on-surface-variant tracking-widest uppercase">Active</span>
          </div>
          <div className="text-3xl font-bold text-on-surface mb-1">{activities?.data?.length || 0}</div>
          <div className="text-sm text-on-surface-variant font-medium">Recent Activity (24h)</div>
          <div className="mt-4 flex items-center -space-x-2">
            <div className="w-6 h-6 rounded-full border-2 border-surface-container-low bg-primary text-[10px] flex items-center justify-center font-bold text-on-primary">AI</div>
            <div className="w-6 h-6 rounded-full border-2 border-surface-container-low bg-tertiary text-[10px] flex items-center justify-center font-bold text-on-tertiary">US</div>
            <div className="w-6 h-6 rounded-full border-2 border-surface-container-low bg-surface-container-highest text-[8px] flex items-center justify-center font-medium">+{Math.max((activities?.data?.length || 0) - 2, 0)}</div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Recent Activity List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-xl font-bold tracking-tight text-on-surface">Recent Activity</h3>
            <button className="text-sm font-medium text-primary hover:underline">View all</button>
          </div>
          
          <div className="bg-surface-container-lowest rounded-xl border border-outline-variant/10 overflow-hidden">
            {activities?.data?.length > 0 ? (
               <div className="divide-y divide-outline-variant/10">
                 {activities.data.map((act: any, idx: number) => {
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
               <div className="p-12 flex flex-col items-center justify-center text-center">
                 <span className="material-symbols-outlined text-4xl text-outline-variant mb-4">inbox</span>
                 <p className="text-on-surface font-medium">No recent activity</p>
                 <p className="text-sm text-on-surface-variant mt-1">Actions taken on this project will appear here.</p>
               </div>
            )}
          </div>
        </div>

        {/* Quick Stats & Breakdown */}
        <div className="space-y-8">
          <div>
            <h3 className="text-xl font-bold tracking-tight mb-6 px-2 text-on-surface">Entity Breakdown</h3>
            <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 space-y-6">
              {Object.keys(entityGroupCounts).length > 0 ? (
                Object.entries(entityGroupCounts).map(([kind, count], idx) => {
                  const colors = ["bg-primary", "bg-tertiary", "bg-secondary", "bg-outline"];
                  return (
                    <div key={kind} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${colors[idx % colors.length]}`}></div>
                        <span className="text-sm font-medium text-on-surface-variant">{kind}</span>
                      </div>
                      <span className="text-sm font-bold text-on-surface">{count as number}</span>
                    </div>
                  );
                })
              ) : (
                <div className="text-sm text-on-surface-variant text-center py-4">No entities discovered yet.</div>
              )}
            </div>
          </div>

          {/* Technical Health Graph Placeholder */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
            <h4 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-6">Graph Integrity</h4>
            <div className="relative h-32 flex items-end gap-1">
              {[40, 60, 55, 80, 95, 75, 85, 90].map((height, idx) => (
                <div key={idx} className="flex-1 bg-primary/20 hover:bg-primary transition-all duration-300 rounded-t" style={{ height: `${height}%` }}></div>
              ))}
            </div>
            <p className="mt-4 text-[10px] text-on-surface-variant text-center">Score: 94.2% Structural Reliability</p>
          </div>

          {/* Integration Status */}
          <div className="bg-primary/5 rounded-xl border border-primary/20 p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="material-symbols-outlined text-primary material-symbols-fill">sensors</span>
              <span className="text-sm font-bold text-on-surface">Real-time Stream</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              <span className="text-xs text-on-surface-variant">Connected to `main` branch analyzer</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
