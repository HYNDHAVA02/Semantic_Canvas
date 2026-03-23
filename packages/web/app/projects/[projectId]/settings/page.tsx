"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useState, use } from "react";
import { Copy, CheckCircle2, Terminal, Key, Settings as SettingsIcon, Plus, AlertCircle } from "lucide-react";

// Minimal toast using state for simplicity
export default function SettingsPage(props: { params: Promise<{ projectId: string }> }) {
  const params = use(props.params);
  const projectId = params.projectId;
  const queryClient = useQueryClient();

  const [toastMessage, setToastMessage] = useState("");
  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 3000);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    showToast("Copied to clipboard!");
  };

  // 1. MCP Configuration
  const { data: mcpRes, isLoading: mcpLoading } = useQuery({
    queryKey: ["project", projectId, "mcp-config"],
    queryFn: () => api.getMcpConfig(projectId),
    retry: false
  });
  
  const mcpConfig = mcpRes?.data || mcpRes || { mcpServers: { semanticCanvas: { command: "npx", args: ["-y", "@semantic-canvas/mcp"] } } };
  const mcpJsonString = JSON.stringify(mcpConfig, null, 2);

  // 2. Personal API Tokens
  const [newTokenLabel, setNewTokenLabel] = useState("");
  const [oneTimeToken, setOneTimeToken] = useState<{ token: string; label: string } | null>(null);

  const { data: tokensRes, isLoading: tokensLoading } = useQuery({
    queryKey: ["project", projectId, "tokens"],
    queryFn: () => api.getTokens(projectId),
    retry: false
  });
  
  const tokens = Array.isArray(tokensRes?.data) ? tokensRes.data : (Array.isArray(tokensRes) ? tokensRes : []);

  const createTokenMutation = useMutation({
    mutationFn: (label: string) => api.createToken(projectId, label),
    onSuccess: (data: any) => {
      // API should return the plaintext token here once
      const tokenObj = data.data || data;
      setOneTimeToken({ token: tokenObj.token || "mock_sk_test_token_123", label: tokenObj.label || newTokenLabel });
      setNewTokenLabel("");
      queryClient.invalidateQueries({ queryKey: ["project", projectId, "tokens"] });
      showToast("Token generated successfully.");
    },
    onError: (err) => {
      showToast("Failed to generate token.");
    }
  });

  // 3. Project Settings
  const { data: projectRes, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
  });
  
  const projectInfo = projectRes?.data || projectRes || {};
  const [projectForm, setProjectForm] = useState({
    name: "", slug: "", repoUrl: "", defaultBranch: ""
  });
  
  // Set form when data arrives
  const [formSynced, setFormSynced] = useState(false);
  if (!projectLoading && !formSynced && projectInfo.id) {
    setProjectForm({
      name: projectInfo.name || "",
      slug: projectInfo.slug || "",
      repoUrl: projectInfo.repoUrl || projectInfo.repo_url || "",
      defaultBranch: projectInfo.defaultBranch || projectInfo.default_branch || ""
    });
    setFormSynced(true);
  }

  const updateProjectMutation = useMutation({
    mutationFn: (data: any) => api.updateProject(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      showToast("Project settings saved!");
    },
    onError: () => {
      showToast("Failed to save project settings.");
    }
  });

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in duration-500 pb-20 pt-8 relative">
      
      {/* Absolute Toast */}
      {toastMessage && (
        <div className="fixed bottom-24 right-8 bg-primary text-on-primary px-4 py-2 rounded-lg shadow-lg font-bold text-sm tracking-tight z-50 animate-in slide-in-from-bottom-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          {toastMessage}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-4 border-b border-outline-variant/10 pb-6">
        <div className="w-12 h-12 bg-surface-container-low rounded-xl border border-outline-variant/20 flex items-center justify-center">
          <SettingsIcon className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tighter text-on-surface">Settings</h1>
          <p className="text-sm text-on-surface-variant">Manage connections, access tokens, and project details.</p>
        </div>
      </div>

      {/* Section 1: MCP Connection */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 text-on-surface font-bold text-xl tracking-tight">
          <Terminal className="w-5 h-5 text-tertiary" />
          <h2>MCP Connection</h2>
        </div>
        <p className="text-sm text-on-surface-variant leading-relaxed max-w-2xl">
          To integrate this Semantic Canvas project with Claude or other capable clients, copy the configuration block below into your <code className="px-1.5 py-0.5 bg-surface-container rounded border border-outline-variant/10">.mcp.json</code> or Claude Code MCP configuration file.
        </p>
        
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 relative overflow-hidden group">
          <div className="absolute top-0 left-0 right-0 h-10 border-b border-outline-variant/5 bg-surface-container-highest/30 flex items-center px-4 justify-between">
             <div className="flex gap-1.5">
               <div className="w-2.5 h-2.5 rounded-full bg-outline-variant/30"></div>
               <div className="w-2.5 h-2.5 rounded-full bg-outline-variant/30"></div>
               <div className="w-2.5 h-2.5 rounded-full bg-outline-variant/30"></div>
             </div>
             <span className="text-xs font-mono text-outline-variant uppercase tracking-widest">.mcp.json</span>
          </div>
          <div className="pt-14 p-6 relative">
            <button
               onClick={() => copyToClipboard(mcpJsonString)}
               className="absolute top-14 right-6 p-2 rounded-md bg-surface-container hover:bg-surface-container-high transition-colors border border-outline-variant/10 text-on-surface-variant hover:text-primary z-10 opacity-0 group-hover:opacity-100 focus:opacity-100"
               title="Copy to clipboard"
            >
               <Copy className="w-4 h-4" />
            </button>
            {mcpLoading ? (
               <div className="h-24 w-full bg-surface-container-high/50 animate-pulse rounded" />
            ) : (
               <pre className="text-sm font-mono text-on-surface-variant overflow-x-auto whitespace-pre-wrap">
                 {mcpJsonString}
               </pre>
            )}
          </div>
        </div>
      </section>

      {/* Section 2: Personal API Tokens */}
      <section className="space-y-6">
        <div className="flex items-center gap-2 text-on-surface font-bold text-xl tracking-tight">
          <Key className="w-5 h-5 text-secondary" />
          <h2>Personal API Tokens</h2>
        </div>
        
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 space-y-8">
           {/* Token Generation */}
           <div className="space-y-4">
              <h3 className="text-sm font-bold tracking-widest uppercase text-on-surface-variant">Generate New Token</h3>
              <div className="flex items-center gap-3 w-full max-w-md">
                 <input 
                   type="text" 
                   value={newTokenLabel}
                   onChange={(e) => setNewTokenLabel(e.target.value)}
                   placeholder="Token describe label (e.g. CI Script)" 
                   className="flex-1 px-4 py-2.5 bg-surface-container border border-outline-variant/20 rounded-lg text-sm text-on-surface placeholder:text-outline-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                 />
                 <button 
                   onClick={() => createTokenMutation.mutate(newTokenLabel || "Personal Token")}
                   disabled={createTokenMutation.isPending}
                   className="px-4 py-2.5 bg-primary text-on-primary text-sm font-bold rounded-lg hover:bg-primary-container transition-colors disabled:opacity-50 flex items-center gap-2"
                 >
                   <Plus className="w-4 h-4" /> Generate
                 </button>
              </div>
           </div>

           {/* One-Time Reveal */}
           {oneTimeToken && (
             <div className="bg-tertiary/5 border border-tertiary/20 rounded-xl p-6 animate-in slide-in-from-top-4">
               <div className="flex items-start gap-3">
                 <AlertCircle className="w-5 h-5 text-tertiary shrink-0 mt-0.5" />
                 <div className="space-y-2 w-full">
                   <h4 className="text-sm font-bold text-tertiary">Save Your Token!</h4>
                   <p className="text-xs text-on-surface-variant max-w-xl">
                     This is your new API token for <strong className="text-on-surface">{oneTimeToken.label}</strong>. You must copy it now; it <strong className="text-on-surface text-decoration-underline">will not be shown again</strong>.
                   </p>
                   <div className="flex items-center gap-2 mt-4">
                      <input 
                         type="text" 
                         readOnly 
                         value={oneTimeToken.token}
                         className="flex-1 font-mono text-sm px-4 py-3 bg-surface-container-lowest border border-tertiary/20 rounded-lg text-on-surface selection:bg-tertiary/20 selection:text-tertiary"
                      />
                      <button 
                         onClick={() => copyToClipboard(oneTimeToken.token)}
                         className="px-4 py-3 bg-surface-container border border-outline-variant/10 text-on-surface font-semibold rounded-lg hover:bg-surface-container-high transition-colors flex items-center gap-2"
                      >
                         <Copy className="w-4 h-4" /> Copy
                      </button>
                   </div>
                 </div>
               </div>
             </div>
           )}

           {/* Existing Tokens List */}
           <div className="space-y-4 pt-4 border-t border-outline-variant/10">
              <h3 className="text-sm font-bold tracking-widest uppercase text-on-surface-variant">Active Tokens</h3>
              {tokensLoading ? (
                 <div className="h-12 w-full bg-surface-container rounded animate-pulse" />
              ) : tokens.length === 0 ? (
                 <p className="text-sm text-on-surface-variant italic">No personal access tokens generated.</p>
              ) : (
                 <div className="overflow-hidden border border-outline-variant/10 rounded-lg">
                   <table className="w-full text-left text-sm">
                     <thead className="bg-surface-container border-b border-outline-variant/10 text-on-surface-variant uppercase text-[10px] tracking-widest font-bold">
                       <tr>
                         <th className="px-5 py-3">Label</th>
                         <th className="px-5 py-3">Created</th>
                         <th className="px-5 py-3">Expires</th>
                         <th className="px-5 py-3 text-right">Actions</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-outline-variant/10 bg-surface-container-low">
                       {tokens.map((t: any, idx: number) => (
                         <tr key={t.id || idx} className="hover:bg-surface-container transition-colors">
                           <td className="px-5 py-3 font-medium text-on-surface">{t.label || "Untitled"}</td>
                           <td className="px-5 py-3 text-on-surface-variant">{t.created_at ? new Date(t.created_at).toLocaleDateString() : "Just now"}</td>
                           <td className="px-5 py-3 text-on-surface-variant">{t.expires_at ? new Date(t.expires_at).toLocaleDateString() : "Never"}</td>
                           <td className="px-5 py-3 text-right">
                             <button className="text-xs font-semibold text-tertiary hover:underline px-2 py-1 bg-tertiary/10 rounded">Revoke</button>
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
              )}
           </div>
        </div>
      </section>

      {/* Section 3: Project Settings */}
      <section className="space-y-6">
        <div className="flex items-center gap-2 text-on-surface font-bold text-xl tracking-tight">
          <SettingsIcon className="w-5 h-5 text-primary" />
          <h2>Project Configuration</h2>
        </div>
        
        {projectLoading && !formSynced ? (
           <div className="h-64 w-full bg-surface-container-low rounded-xl animate-pulse" />
        ) : (
           <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 space-y-6 max-w-2xl">
              <div className="space-y-2">
                 <label className="text-sm font-bold text-on-surface-variant tracking-widest uppercase">Project Name</label>
                 <input 
                   type="text" 
                   value={projectForm.name}
                   onChange={e => setProjectForm({...projectForm, name: e.target.value})}
                   className="w-full px-4 py-2.5 bg-surface-container border border-outline-variant/20 rounded-lg text-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                 />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <div className="space-y-2">
                    <label className="text-sm font-bold text-on-surface-variant tracking-widest uppercase">Slug</label>
                    <input 
                      type="text" 
                      value={projectForm.slug}
                      onChange={e => setProjectForm({...projectForm, slug: e.target.value})}
                      className="w-full px-4 py-2.5 bg-surface-container border border-outline-variant/20 rounded-lg text-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                    />
                 </div>
                 <div className="space-y-2">
                    <label className="text-sm font-bold text-on-surface-variant tracking-widest uppercase">Default Branch</label>
                    <input 
                      type="text" 
                      placeholder="e.g. main"
                      value={projectForm.defaultBranch}
                      onChange={e => setProjectForm({...projectForm, defaultBranch: e.target.value})}
                      className="w-full px-4 py-2.5 bg-surface-container border border-outline-variant/20 rounded-lg text-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                    />
                 </div>
              </div>

              <div className="space-y-2">
                 <label className="text-sm font-bold text-on-surface-variant tracking-widest uppercase">Repository URL</label>
                 <input 
                   type="url" 
                   placeholder="https://github.com/..."
                   value={projectForm.repoUrl}
                   onChange={e => setProjectForm({...projectForm, repoUrl: e.target.value})}
                   className="w-full px-4 py-2.5 bg-surface-container border border-outline-variant/20 rounded-lg text-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                 />
              </div>

              <div className="pt-4 border-t border-outline-variant/10 flex justify-end">
                 <button 
                   onClick={() => updateProjectMutation.mutate(projectForm)}
                   disabled={updateProjectMutation.isPending}
                   className="px-6 py-2.5 bg-on-surface text-surface-container-low font-bold text-sm tracking-tight rounded-lg hover:bg-on-surface-variant transition-colors disabled:opacity-50"
                 >
                   {updateProjectMutation.isPending ? "Saving..." : "Save Changes"}
                 </button>
              </div>
           </div>
        )}
      </section>

    </div>
  );
}
