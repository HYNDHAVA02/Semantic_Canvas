"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X, FolderOpen, GitBranch } from "lucide-react";
import Link from "next/link";
import AuthGuard from "@/components/auth-guard";

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    slug: "",
    description: "",
    repo_url: "",
    default_branch: "main",
  });

  const { data: projectsRes, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.getProjects(),
  });

  const projects = projectsRes?.data || [];

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.createProject(data),
    onSuccess: (result: any) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      const newId = result?.id || result?.data?.id;
      if (newId) {
        router.push(`/projects/${newId}`);
      } else {
        setShowForm(false);
        setFormData({ name: "", slug: "", description: "", repo_url: "", default_branch: "main" });
      }
    },
  });

  const handleNameChange = (name: string) => {
    setFormData((prev) => ({ ...prev, name, slug: toSlug(name) }));
  };

  return (
    <AuthGuard>
      <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 py-12 px-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-2 text-on-surface">
            <h1 className="text-4xl font-extrabold tracking-tighter">Projects</h1>
            <p className="text-on-surface-variant max-w-2xl">
              Your knowledge bases — each project maps to a codebase.
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container transition-colors flex items-center justify-center gap-2"
          >
            {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {showForm ? "Cancel" : "Create Project"}
          </button>
        </div>

        {/* Inline Form */}
        {showForm && (
          <div className="bg-surface-container-high/50 p-6 rounded-xl border border-secondary/20 space-y-4 animate-in slide-in-from-top-4">
            <h3 className="text-sm font-bold tracking-widest text-primary uppercase">New Project</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-on-surface-variant uppercase tracking-widest">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="My Project"
                  className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-on-surface-variant uppercase tracking-widest">Slug</label>
                <input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  placeholder="my-project"
                  className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="space-y-1 md:col-span-2">
                <label className="text-xs font-medium text-on-surface-variant uppercase tracking-widest">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="What is this project about?"
                  rows={2}
                  className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-on-surface-variant uppercase tracking-widest">Repository URL</label>
                <input
                  type="url"
                  value={formData.repo_url}
                  onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
                  placeholder="https://github.com/org/repo.git"
                  className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-on-surface-variant uppercase tracking-widest">Default Branch</label>
                <input
                  type="text"
                  value={formData.default_branch}
                  onChange={(e) => setFormData({ ...formData, default_branch: e.target.value })}
                  placeholder="main"
                  className="w-full px-4 py-2 bg-surface-container border border-outline-variant/10 rounded-lg text-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
            <button
              onClick={() => createMutation.mutate(formData)}
              disabled={createMutation.isPending || !formData.name || !formData.slug}
              className="px-6 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary/80 transition-colors disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating..." : "Create Project"}
            </button>
            {createMutation.isError && (
              <p className="text-sm text-error">{(createMutation.error as Error).message}</p>
            )}
          </div>
        )}

        {/* Projects Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 animate-pulse space-y-3">
                <div className="h-5 w-40 bg-surface-container-high rounded" />
                <div className="h-4 w-full bg-surface-container rounded" />
                <div className="h-4 w-24 bg-surface-container rounded" />
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-4 border-2 border-dashed border-outline-variant/10 rounded-xl p-16">
            <FolderOpen className="w-16 h-16 text-outline-variant" />
            <h3 className="text-lg font-bold text-on-surface">No projects yet</h3>
            <p className="text-sm text-on-surface-variant">Create your first one to get started.</p>
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project: any) => (
              <Link
                key={project.id}
                href={`/projects/${project.id}`}
                className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 hover:bg-surface-container transition-colors group space-y-3"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant/20 flex items-center justify-center shrink-0 text-primary">
                    <FolderOpen className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-bold text-on-surface truncate group-hover:text-primary transition-colors">
                      {project.name}
                    </h3>
                    <p className="text-xs text-on-surface-variant">{project.slug}</p>
                  </div>
                </div>
                {project.description && (
                  <p className="text-sm text-on-surface-variant line-clamp-2">{project.description}</p>
                )}
                {project.repo_url && (
                  <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
                    <GitBranch className="w-3 h-3" />
                    <span className="truncate">{project.repo_url.replace(/^https?:\/\//, "")}</span>
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
