"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState, use } from "react";
import { GitFork, Plus, X, ArrowRight } from "lucide-react";
import Link from "next/link";

// Display labels for known relationship kinds
const KIND_LABELS: Record<string, string> = {
  calls: "Calls",
  depends_on: "Depends On",
  reads_from: "Reads From",
  imports: "Imports",
  inherits: "Inherits",
  implements: "Implements",
  owns: "Owns",
  writes_to: "Writes To",
};

const kindColors: Record<string, string> = {
  calls: "bg-primary/10 text-primary border-primary/20",
  depends_on: "bg-tertiary/10 text-tertiary border-tertiary/20",
  reads_from: "bg-secondary/10 text-secondary border-secondary/20",
  imports: "bg-outline-variant/10 text-on-surface border-outline-variant/20",
  inherits: "bg-primary-container/10 text-primary border-primary-container/20",
};

export default function RelationshipsPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const queryClient = useQueryClient();

  const [kindFilter, setKindFilter] = useState("All");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ from_entity_id: "", to_entity_id: "", kind: "calls" });

  const { data: relationshipsRes, isLoading } = useQuery({
    queryKey: ["project", projectId, "relationships"],
    queryFn: () => api.getProjectRelationships(projectId),
  });

  const { data: entitiesRes } = useQuery({
    queryKey: ["project", projectId, "entities", 1000],
    queryFn: () => api.getProjectEntities(projectId, 1000),
  });

  const relationships = relationshipsRes?.data || [];
  const entities = entitiesRes?.data || [];

  // Build filter options dynamically from the actual data
  const distinctKinds: string[] = [...new Set<string>(relationships.map((r: any) => String(r.kind)))].sort();
  const filterOptions = ["All", ...distinctKinds.map((k: string) => KIND_LABELS[k] || k)];
  // Reverse lookup: display label → raw kind value
  const labelToValue: Record<string, string> = {};
  for (const k of distinctKinds) {
    labelToValue[KIND_LABELS[k] || k] = k;
  }

  const filteredRelationships = kindFilter === "All"
    ? relationships
    : relationships.filter((r: any) => r.kind === labelToValue[kindFilter]);

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createRelationship(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId, "relationships"] });
      setShowForm(false);
      setFormData({ from_entity_id: "", to_entity_id: "", kind: "calls" });
    },
  });

  const entityName = (id: string) => {
    const e = entities.find((e: any) => e.id === id);
    return e?.name || id.slice(0, 8);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-2 text-on-surface">
          <div className="flex items-center gap-2">
            <GitFork className="w-6 h-6 text-primary" />
            <h1 className="text-4xl font-extrabold tracking-tighter">Relationships</h1>
          </div>
          <p className="text-on-surface-variant max-w-2xl">
            Connections between entities — calls, dependencies, imports, and inheritance.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container transition-colors flex items-center justify-center gap-2"
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? "Cancel" : "Add Relationship"}
        </button>
      </div>

      {/* Inline Form */}
      {showForm && (
        <div className="bg-surface-container-high/50 p-6 rounded-xl border border-secondary/20 space-y-4 animate-in slide-in-from-top-4">
          <h3 className="text-sm font-bold tracking-widest text-primary uppercase">New Relationship</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <select
              value={formData.from_entity_id}
              onChange={(e) => setFormData({ ...formData, from_entity_id: e.target.value })}
              className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary text-on-surface"
            >
              <option value="">From entity...</option>
              {entities.map((e: any) => (
                <option key={e.id} value={e.id}>{e.name}</option>
              ))}
            </select>
            <select
              value={formData.to_entity_id}
              onChange={(e) => setFormData({ ...formData, to_entity_id: e.target.value })}
              className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary text-on-surface"
            >
              <option value="">To entity...</option>
              {entities.map((e: any) => (
                <option key={e.id} value={e.id}>{e.name}</option>
              ))}
            </select>
            <select
              value={formData.kind}
              onChange={(e) => setFormData({ ...formData, kind: e.target.value })}
              className="px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary text-on-surface"
            >
              {Object.entries(KIND_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => createMutation.mutate(formData)}
            disabled={createMutation.isPending || !formData.from_entity_id || !formData.to_entity_id}
            className="px-6 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary/80 transition-colors disabled:opacity-50"
          >
            {createMutation.isPending ? "Creating..." : "Save Relationship"}
          </button>
        </div>
      )}

      {/* Kind Filter */}
      <div className="flex flex-wrap items-center gap-2 p-1 bg-surface-container-low rounded-lg border border-outline-variant/10 w-fit shrink-0 max-w-full overflow-auto">
        {filterOptions.map((k) => (
          <button
            key={k}
            onClick={() => setKindFilter(k)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium tracking-tight transition-colors whitespace-nowrap ${
              kindFilter === k
                ? "bg-surface-container-highest text-primary shadow-sm"
                : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
            }`}
          >
            {k}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-outline-variant/10 bg-surface-container text-on-surface-variant tracking-widest uppercase text-xs">
                <th className="px-6 py-4 font-medium">From → To</th>
                <th className="px-6 py-4 font-medium">Kind</th>
                <th className="px-6 py-4 font-medium hidden sm:table-cell">Source</th>
                <th className="px-6 py-4 font-medium text-right">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-4"><div className="h-4 w-56 bg-surface-container-high rounded" /></td>
                    <td className="px-6 py-4"><div className="h-4 w-20 bg-surface-container-high rounded" /></td>
                    <td className="px-6 py-4 hidden sm:table-cell"><div className="h-4 w-24 bg-surface-container-high rounded" /></td>
                    <td className="px-6 py-4 flex justify-end"><div className="h-4 w-20 bg-surface-container-high rounded" /></td>
                  </tr>
                ))
              ) : filteredRelationships.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-outline-variant/10 rounded-xl p-12 mx-4 my-2">
                      <GitFork className="w-12 h-12 text-outline-variant" />
                      <h3 className="text-lg font-bold text-on-surface">No Relationships Found</h3>
                      <p className="text-sm text-on-surface-variant">Try another filter or add a new relationship.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredRelationships.map((rel: any) => {
                  const kindStyle = kindColors[rel.kind] || "bg-outline-variant/10 text-on-surface border-outline-variant/20";
                  return (
                    <tr key={rel.id} className="hover:bg-surface-container transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 font-medium text-on-surface">
                          <Link
                            href={`/projects/${projectId}/entities/${rel.from_entity_id}`}
                            className="hover:text-primary transition-colors"
                          >
                            {entityName(rel.from_entity_id)}
                          </Link>
                          <ArrowRight className="w-4 h-4 text-outline-variant shrink-0" />
                          <Link
                            href={`/projects/${projectId}/entities/${rel.to_entity_id}`}
                            className="hover:text-primary transition-colors"
                          >
                            {entityName(rel.to_entity_id)}
                          </Link>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-widest border ${kindStyle}`}>
                          {rel.kind}
                        </span>
                      </td>
                      <td className="px-6 py-4 hidden sm:table-cell text-on-surface-variant">
                        {rel.source || "System"}
                      </td>
                      <td className="px-6 py-4 text-right text-on-surface-variant whitespace-nowrap">
                        {rel.created_at ? new Date(rel.created_at).toLocaleDateString() : "Just now"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {!isLoading && filteredRelationships.length > 0 && (
          <div className="p-4 border-t border-outline-variant/10 flex items-center justify-between text-xs text-on-surface-variant">
            <span>Showing {filteredRelationships.length} relationships</span>
          </div>
        )}
      </div>
    </div>
  );
}
