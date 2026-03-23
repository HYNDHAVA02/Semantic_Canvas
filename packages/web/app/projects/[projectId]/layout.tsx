"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, use } from "react";

export default function ProjectLayout(props: {
  children: ReactNode;
  params: Promise<{ projectId: string }>;
}) {
  const { children } = props;
  const pathname = usePathname();
  const params = use(props.params);
  const projectId = params.projectId || "403f22ef-a063-42d3-bf6e-8c529eb05c0b";

  const navigation = [
    { name: "Overview", href: `/projects/${projectId}`, icon: "dashboard" },
    { name: "Entities", href: `/projects/${projectId}/entities`, icon: "database" },
    { name: "Relationships", href: `/projects/${projectId}/relationships`, icon: "account_tree" },
    { name: "Decisions", href: `/projects/${projectId}/decisions`, icon: "gavel" },
    { name: "Conventions", href: `/projects/${projectId}/conventions`, icon: "rule" },
    { name: "Activity", href: `/projects/${projectId}/activity`, icon: "history" },
  ];

  const bottomNavigation = [
    { name: "Home", href: `/projects/${projectId}`, icon: "dashboard" },
    { name: "Canvas", href: `/projects/${projectId}/relationships`, icon: "account_tree" },
    { name: "Log", href: `/projects/${projectId}/activity`, icon: "history" },
    { name: "Menu", href: `/projects/${projectId}/settings`, icon: "settings" },
  ];

  const secondaryNav = [
    { name: "Search", href: `/projects/${projectId}/search`, icon: "search" },
    { name: "Settings", href: `/projects/${projectId}/settings`, icon: "settings" },
  ];

  return (
    <>
      <nav className="hidden md:flex h-screen w-64 fixed left-0 top-0 bg-surface-container-low flex-col py-6 gap-1 z-50 overflow-y-auto">
        <div className="px-6 mb-8">
          <span className="text-xl font-bold tracking-tighter text-on-surface">Semantic Canvas</span>
        </div>
        <div className="flex flex-col gap-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`mx-2 px-3 py-2 font-['Inter'] tracking-tight text-sm font-medium flex items-center gap-3 transition-colors duration-150 rounded-md
                  ${isActive ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50"}`}
              >
                <span className="material-symbols-outlined text-lg">{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>
        <div className="mt-auto flex flex-col gap-1">
          {secondaryNav.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`mx-2 px-3 py-2 font-['Inter'] tracking-tight text-sm font-medium flex items-center gap-3 transition-colors duration-150 rounded-md
                  ${isActive ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50"}`}
              >
                <span className="material-symbols-outlined text-lg">{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      <header className="fixed top-0 right-0 left-0 md:left-64 h-16 z-40 bg-background/80 backdrop-blur-md border-b border-outline-variant/15 flex items-center justify-between px-8 transition-all">
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-primary md:hidden cursor-pointer">menu</span>
          <h1 className="text-lg font-bold text-on-surface font-['Inter'] tracking-tight">Project Dashboard</h1>
        </div>
        <div className="flex items-center gap-6">
          <Link href={`/projects/${projectId}/search`}>
            <span className="material-symbols-outlined text-on-surface-variant hover:text-on-surface cursor-pointer transition">search</span>
          </Link>
          <div className="h-8 w-8 rounded-full bg-surface-container-highest border border-outline-variant/20 flex items-center justify-center text-xs font-bold text-primary">SC</div>
        </div>
      </header>

      <main className="pt-24 pb-20 md:pb-12 px-6 md:px-12 ml-0 md:ml-64 min-h-screen">
        {children}
      </main>

      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-surface-container-low border-t border-outline-variant/10 flex items-center justify-around px-4 z-50">
        {bottomNavigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href} className={`flex flex-col items-center gap-1 ${isActive ? "text-primary" : "text-on-surface-variant"}`}>
              <span className={`material-symbols-outlined text-2xl ${isActive ? "material-symbols-fill" : ""}`}>{item.icon}</span>
              <span className="text-[10px] font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
