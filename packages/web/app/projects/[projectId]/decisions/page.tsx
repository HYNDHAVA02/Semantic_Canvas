"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useState, use } from "react";
import { Gavel, Plus, X } from "lucide-react";

export default function DecisionsPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const queryClient = useQueryClient();

  const [tagFilter, setTagFilter] = useState("All");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ title: "", body: "", tags: "", decidedBy: "" });

  const { data: decisionsRes, isLoading } = useQuery({
    queryKey: ["project", projectId, "decisions"],
    queryFn: () => api.getProjectDecisions(projectId, 100),
  });

  const decisions = Array.isArray(decisionsRes?.data) ? decisionsRes.data : (Array.isArray(decisionsRes) ? decisionsRes : []);

  // Filter Logic
  const filteredDecisions = tagFilter === "All" 
    ? decisions 
    : decisions.filter((d: any) => {
        const dTags = Array.isArray(d.tags) ? d.tags : (d.tags ? d.tags.split(',').map((t: string) => t.trim()) : []);
        return dTags.some((t: string) => t.toLowerCase() === tagFilter.toLowerCase());
      });

  // Extract unique tags for filter buttons
  const allTags = new Set<string>();
  decisions.forEach((d: any) => {
    const dTags = Array.isArray(d.tags) ? d.tags : (d.tags ? d.tags.split(',').map((t: string) => t.trim()) : []);
    dTags.forEach((t: string) => { if (t) allTags.add(t); });
  });
  const filterOptions = ["All", ...Array.from(allTags)];

  const createDecisionMutation = useMutation({
    mutationFn: (data: any) => api.createDecision(projectId, {
      title: data.title,
      body: data.body,
      decided_by: data.decidedBy,
      tags: data.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId, "decisions"] });
      setShowForm(false);
      setFormData({ title: "", body: "", tags: "", decidedBy: "" });
    }
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-2 text-on-surface">
          <div className="flex items-center gap-2">
            <Gavel className="w-6 h-6 text-tertiary" />
            <h1 className="text-4xl font-extrabold tracking-tighter">Decisions</h1>
          </div>
          <p className="text-on-surface-variant max-w-2xl">
            Architectural Design Records (ADRs) tracking key technical choices.
          </p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container transition-colors flex items-center justify-center gap-2"
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? "Cancel" : "Log Decision"}
        </button>
      </div>

      {showForm && (
        <div className="bg-surface-container-high/50 p-6 rounded-xl border border-tertiary/20 space-y-4 animate-in slide-in-from-top-4">
          <h3 className="text-sm font-bold tracking-widest text-tertiary uppercase">Create New Decision</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="Decision Title" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-tertiary" />
            <input placeholder="Decided By (Agent, User, Team)" value={formData.decidedBy} onChange={e => setFormData({...formData, decidedBy: e.target.value})} className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-tertiary" />
          </div>
          <textarea placeholder="Rationale and detailed context..." value={formData.body} onChange={e => setFormData({...formData, body: e.target.value})} className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm min-h-24 focus:outline-none focus:ring-1 focus:ring-tertiary" />
          <input placeholder="Tags (comma separated, e.g. frontend, auth)" value={formData.tags} onChange={e => setFormData({...formData, tags: e.target.value})} className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-tertiary" />
          <button 
            onClick={() => createDecisionMutation.mutate(formData)}
            disabled={createDecisionMutation.isPending || !formData.title}
            className="px-6 py-2 bg-tertiary text-on-tertiary text-sm font-bold rounded-lg hover:bg-tertiary-container transition-colors disabled:opacity-50"
          >
             {createDecisionMutation.isPending ? "Saving..." : "Save Record"}
          </button>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="flex flex-wrap items-center gap-2 p-1 bg-surface-container-low rounded-lg border border-outline-variant/10 w-fit shrink-0 max-w-full overflow-auto">
        {filterOptions.map((f) => (
          <button
            key={f}
            onClick={() => setTagFilter(f)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium tracking-tight transition-colors whitespace-nowrap ${
              tagFilter === f 
                ? "bg-surface-container-highest text-tertiary shadow-sm" 
                : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Cards List */}
      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="p-6 bg-surface-container-low rounded-xl border border-outline-variant/10 animate-pulse space-y-4">
               <div className="h-5 w-48 bg-surface-container-high rounded" />
               <div className="h-4 w-full bg-surface-container rounded" />
               <div className="flex gap-2"><div className="w-12 h-4 rounded bg-tertiary/20" /></div>
            </div>
          ))
        ) : filteredDecisions.length === 0 ? (
          <div className="p-16 text-center border-2 border-dashed border-outline-variant/10 rounded-xl bg-surface-container-low">
             <Gavel className="w-12 h-12 text-outline-variant mx-auto mb-4" />
             <h3 className="text-lg font-bold text-on-surface">No Decisions Logged</h3>
             <p className="text-sm text-on-surface-variant mt-1">Refine your filters or create a new Design Record.</p>
          </div>
        ) : (
          filteredDecisions.map((d: any) => {
             const dTags = Array.isArray(d.tags) ? d.tags : (d.tags ? d.tags.split(',').map((t: string) => t.trim()) : []);
             
             return (
               <div key={d.id || Math.random()} className="p-6 bg-surface-container-low rounded-xl border border-outline-variant/10 hover:border-tertiary/30 transition-all group">
                  <div className="flex items-start justify-between gap-4 mb-2">
                     <h3 className="text-lg font-bold text-on-surface group-hover:text-tertiary transition-colors">{d.title || "Untitled"}</h3>
                     <span className="text-xs font-semibold text-on-surface-variant whitespace-nowrap">
                       {d.created_at ? new Date(d.created_at).toLocaleDateString() : "Just now"}
                     </span>
                  </div>
                  <p className="text-sm text-on-surface-variant leading-relaxed line-clamp-3 mb-4">
                    {d.body || d.rationale || "No context provided."}
                  </p>
                  <div className="flex items-center justify-between border-t border-outline-variant/10 pt-4 mt-2">
                     <div className="flex flex-wrap items-center gap-2">
                        {dTags.map((tag: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 rounded text-[10px] uppercase tracking-widest font-bold bg-tertiary/10 text-tertiary border border-tertiary/20">{tag}</span>
                        ))}
                     </div>
                     <span className="text-xs text-on-surface-variant font-medium">Decided by <strong className="text-on-surface">{d.decided_by || "System"}</strong></span>
                  </div>
               </div>
             )
          })
        )}
      </div>
    </div>
  );
}
