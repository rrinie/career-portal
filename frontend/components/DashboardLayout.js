"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { isAuthenticated, getStoredUser, clearSession } from "../lib/api";

// ─── Icons (inline SVG — no icon package dependency) ─────────────────────────
const Icons = {
  Jobs: () => (
    <svg className="nav-icon w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  Applications: () => (
    <svg className="nav-icon w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  Profile: () => (
    <svg className="nav-icon w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
  Interviews: () => (
    <svg className="nav-icon w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.868v6.264a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  ),
  Dashboard: () => (
    <svg className="nav-icon w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
    </svg>
  ),
  Logout: () => (
    <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  ),
  Logo: () => (
    <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#4f6ef7" />
      <path d="M8 22L14 10L20 18L24 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="24" cy="14" r="2.5" fill="white" />
    </svg>
  ),
};

// ─── Nav items per actor type ─────────────────────────────────────────────────
const SEEKER_NAV = [
  { href: "/jobs",         label: "Job Board",    Icon: Icons.Jobs },
  { href: "/applications", label: "Applications", Icon: Icons.Applications },
  { href: "/interviews",   label: "Interviews",   Icon: Icons.Interviews },
  { href: "/profile",      label: "My Profile",   Icon: Icons.Profile },
];

const COMPANY_NAV = [
  { href: "/jobs",      label: "Job Board",   Icon: Icons.Jobs },
  { href: "/postings",  label: "My Postings", Icon: Icons.Dashboard },
  { href: "/candidates",label: "Candidates",  Icon: Icons.Applications },
  { href: "/profile",   label: "Company",     Icon: Icons.Profile },
];

// ─── User avatar initials ─────────────────────────────────────────────────────
function Avatar({ user }) {
  const initials = user
    ? (
        user.actorType === "company"
          ? (user.CompanyName || "C").slice(0, 2).toUpperCase()
          : `${user.FirstName?.[0] ?? ""}${user.LastName?.[0] ?? ""}`.toUpperCase()
      )
    : "?";

  return (
    <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
      <span className="text-white text-xs font-bold">{initials}</span>
    </div>
  );
}

// ─── Section divider ──────────────────────────────────────────────────────────
function NavSection({ label }) {
  return (
    <div className="px-5 pt-5 pb-1">
      <span className="text-slate-600 text-[10.5px] font-semibold uppercase tracking-widest">
        {label}
      </span>
    </div>
  );
}

// ─── Main layout ──────────────────────────────────────────────────────────────
export default function DashboardLayout({ children }) {
  const router   = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // isAuthenticated() and getStoredUser() read localStorage synchronously.
    // This effect must run once on mount — after the browser has painted and
    // localStorage is fully accessible from the JS context.
    //
    // router is intentionally excluded from the dep array: in Next.js App
    // Router the router object gets a new reference on every render, so
    // including it would cause this guard to re-fire during navigation,
    // creating a window where ready=false and triggering a spurious /login
    // redirect even when the token is present.
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setUser(getStoredUser());
    setReady(true);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };

  if (!ready) {
    // Skeleton splash — prevents layout flash during auth check
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400 text-sm">
          <svg className="animate-spin h-4 w-4 text-accent" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          Loading…
        </div>
      </div>
    );
  }

  const isCompany = user?.actorType === "company";
  const navItems  = isCompany ? COMPANY_NAV : SEEKER_NAV;

  const displayName = isCompany
    ? user?.CompanyName
    : `${user?.FirstName ?? ""} ${user?.LastName ?? ""}`.trim();

  const roleLabel = isCompany ? "Company Account" : "Job Seeker";

  return (
    <div className="flex min-h-screen">

      {/* ── Sidebar ────────────────────────────────────────────────── */}
      <aside className="sidebar">

        {/* Logo */}
        <div className="flex items-center gap-3 px-5 h-14 border-b border-slate-800 flex-shrink-0">
          <Icons.Logo />
          <div>
            <div className="text-white text-sm font-semibold leading-none">Career Portal</div>
            <div className="text-slate-500 text-[10px] mt-0.5">University Platform</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3">
          <NavSection label="Navigation" />
          {navItems.map(({ href, label, Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={`sidebar-nav-item ${active ? "active" : ""}`}
              >
                <Icon />
                <span>{label}</span>
                {active && (
                  <span className="ml-auto w-1 h-1 rounded-full bg-accent" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="border-t border-slate-800 p-3 flex-shrink-0">
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg mb-1">
            <Avatar user={user} />
            <div className="flex-1 min-w-0">
              <div className="text-slate-200 text-xs font-semibold truncate">{displayName}</div>
              <div className="text-slate-500 text-[10.5px] truncate">{roleLabel}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="sidebar-nav-item w-full text-left hover:!text-red-400 hover:!bg-red-900/20 group"
          >
            <Icons.Logout />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* ── Main content ───────────────────────────────────────────── */}
      <main className="main-shell flex-1">
        {children}
      </main>

    </div>
  );
}
