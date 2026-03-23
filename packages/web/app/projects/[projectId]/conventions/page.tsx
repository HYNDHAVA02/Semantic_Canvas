"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useState, use } from "react";
import { Ruler, Plus, X, Check, XCircle } from "lucide-react";

export default function ConventionsPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const queryClient = useQueryClient();

  const scopes = ["All", "Global", "Backend", "Frontend", "Database"];
  const [scopeFilter, setScopeFilter] = useState("All");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ title: "", body: "", scope: "Global", tags: "" });

  const { data: conventionsRes, isLoading } = useQuery({
    queryKey: ["project", projectId, "conventions"],
    queryFn: () => api.getProjectConventions(projectId),
  });

  const conventions = Array.isArray(conventionsRes?.data) ? conventionsRes.data : (Array.isArray(conventionsRes) ? conventionsRes : []);

  const filteredConventions = scopeFilter === "All" 
    ? conventions 
    : conventions.filter((c: any) => c.scope?.toLowerCase() === scopeFilter.toLowerCase());

  const createStatus = useMutation({
    mutationFn: (data: any) => api.createConvention(projectId, {
      title: data.title,
      body: data.body,
      scope: data.scope,
      tags: data.tags.split(',').map((t: string) => t.trim()).filter(Boolean),
      active: true
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId, "conventions"] });
      setShowForm(false);
      setFormData({ title: "", body: "", scope: "Global", tags: "" });
    }
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, active }: { id: string, active: boolean }) => api.updateConvention(projectId, id, { active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId, "conventions"] });
    }
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-2 text-on-surface">
          <div className="flex items-center gap-2">
            <Ruler className="w-6 h-6 text-secondary" />
            <h1 className="text-4xl font-extrabold tracking-tighter">Conventions</h1>
          </div>
          <p className="text-on-surface-variant max-w-2xl">
            Team rules, style constraints, and documented engineering practices.
          </p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container transition-colors flex items-center justify-center gap-2"
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? "Cancel" : "Add Convention"}
        </button>
      </div>

      {showForm && (
        <div className="bg-surface-container-high/50 p-6 rounded-xl border border-secondary/20 space-y-4 animate-in slide-in-from-top-4">
          <h3 className="text-sm font-bold tracking-widest text-secondary uppercase">Define New Rule</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="Rule Title / Convention Name" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            <select value={formData.scope} onChange={e => setFormData({...formData, scope: e.target.value})} className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-secondary text-on-surface">
               {scopes.filter(s => s !== "All").map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <textarea placeholder="Rule description and enforcement details..." value={formData.body} onChange={e => setFormData({...formData, body: e.target.value})} className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm min-h-24 focus:outline-none focus:ring-1 focus:ring-secondary" />
          <input placeholder="Tags (comma separated)" value={formData.tags} onChange={e => setFormData({...formData, tags: e.target.value})} className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
          <button 
            onClick={() => createStatus.mutate(formData)}
            disabled={createStatus.isPending || !formData.title}
            className="px-6 py-2 bg-secondary text-on-secondary text-sm font-bold rounded-lg hover:bg-secondary/80 transition-colors disabled:opacity-50"
          >
             {createStatus.isPending ? "Creating..." : "Save Convention"}
          </button>
        </div>
      )}

      {/* Scope Filter Buttons */}
      <div className="flex flex-wrap items-center gap-2 p-1 bg-surface-container-low rounded-lg border border-outline-variant/10 w-fit shrink-0 max-w-full overflow-auto">
        {scopes.map((s) => (
          <button
            key={s}
            onClick={() => setScopeFilter(s)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium tracking-tight transition-colors whitespace-nowrap ${
              scopeFilter === s 
                ? "bg-surface-container-highest text-secondary shadow-sm" 
                : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-6 bg-surface-container-low rounded-xl border border-outline-variant/10 animate-pulse space-y-4">
               <div className="h-5 w-3/4 bg-surface-container-high rounded" />
               <div className="h-4 w-full bg-surface-container rounded" />
               <div className="flex justify-between mt-4">
                  <div className="w-16 h-4 bg-secondary/20 rounded" />
                  <div className="w-12 h-6 bg-surface-container rounded-full" />
               </div>
            </div>
          ))
        ) : filteredConventions.length === 0 ? (
          <div className="col-span-full p-16 text-center border-2 border-dashed border-outline-variant/10 rounded-xl bg-surface-container-low">
             <Ruler className="w-12 h-12 text-outline-variant mx-auto mb-4" />
             <h3 className="text-lg font-bold text-on-surface">No Conventions Found</h3>
             <p className="text-sm text-on-surface-variant mt-1">Check another scope or extract conventions natively.</p>
          </div>
        ) : (
          filteredConventions.map((c: any) => {
             const isActive = c.active !== false; // defaults true
             
             return (
               <div key={c.id || Math.random()} className={`p-6 rounded-xl border transition-all flex flex-col justify-between ${isActive ? 'bg-surface-container-low border-outline-variant/10 hover:border-secondary/30' : 'bg-surface-container-lowest border-outline-variant/5 opacity-50'}`}>
                 <div className="mb-4 space-y-2">
                    <div className="flex justify-between items-start gap-2">
                        <h3 className="text-lg font-bold text-on-surface leading-tight">{c.title || "Untitled"}</h3>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest text-on-surface-variant bg-surface-container border border-outline-variant/10">
                          {c.scope || "Global"}
                        </span>
                    </div>
                    <p className="text-sm text-on-surface-variant line-clamp-3 leading-relaxed">
                      {c.body || "No rule definition..."}
                    </p>
                 </div>

                 <div className="border-t border-outline-variant/5 pt-4 flex items-center justify-between">
                    <span className={`text-xs font-bold uppercase tracking-widest flex items-center gap-1 ${isActive ? "text-primary" : "text-outline-variant"}`}>
                       <span className="relative flex h-2 w-2">
                         {isActive && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>}
                         <span className={`relative inline-flex rounded-full h-2 w-2 ${isActive ? "bg-primary" : "bg-outline-variant"}`}></span>
                       </span>
                       {isActive ? "Active" : "Retired"}
                    </span>
                    <button 
                      onClick={() => updateStatus.mutate({ id: c.id, active: !isActive })}
                      className="px-3 py-1 bg-surface-container hover:bg-surface-container-high transition-colors text-[10px] font-bold tracking-wider text-on-surface rounded border border-outline-variant/10 uppercase"
                    >
                      {isActive ? "Retire Rule" : "Restore"}
                    </button>
                 </div>
               </div>
             )
          })
        )}
      </div>
    </div>
  );
}
