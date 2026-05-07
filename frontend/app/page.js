"use client";

/**
 * app/page.js  —  Root entry point
 * ---------------------------------
 * This component has exactly one job: read localStorage on mount and
 * send the user to the right place immediately.
 *
 * Why "use client" + useEffect instead of a server redirect?
 *   isAuthenticated() reads localStorage, which only exists in the browser.
 *   A server component cannot access it, so the check must happen client-side
 *   inside a useEffect (the first point at which the browser context is live).
 *
 * Why router.replace instead of router.push?
 *   replace() overwrites this entry in the browser history stack so the user
 *   cannot press Back and land here again — they always end up at /jobs or
 *   /login, never on a blank routing screen.
 *
 * Why empty dep array on the useEffect?
 *   The check is instantaneous and only needs to run once — on mount.
 *   Including `router` in the dep array would cause re-fires on every render
 *   because Next.js App Router returns a new router reference each render,
 *   which risks an infinite loop. See the same pattern in DashboardLayout.js.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "../lib/api";

// ─── Logo mark — matches login/page.js exactly ───────────────────────────────
function LogoMark() {
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="8" fill="#4f6ef7" />
      <path
        d="M8 22L14 10L20 18L24 14"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="24" cy="14" r="2.5" fill="white" />
    </svg>
  );
}

// ─── Animated ring spinner ────────────────────────────────────────────────────
function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-accent"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-label="Loading"
    >
      <circle
        className="opacity-20"
        cx="12" cy="12" r="10"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        className="opacity-80"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8z"
      />
    </svg>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function RootPage() {
  const router = useRouter();

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    // localStorage is synchronous — no await needed.
    // The redirect fires in the same tick as the effect, so the loading
    // screen is visible only for the duration of the Next.js navigation
    // transition (typically < 100 ms).
    if (isAuthenticated()) {
      router.replace("/jobs");
    } else {
      router.replace("/login");
    }
  }, []);

  // ── Loading screen ───────────────────────────────────────────────────────
  // Rendered only during the brief navigation transition.
  // Matches the bg-slate-50 base established in globals.css.
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center gap-6">

      {/* Brand mark */}
      <div className="flex flex-col items-center gap-3 animate-fade-in">
        <LogoMark />
        <div className="text-center">
          <p className="text-slate-800 text-sm font-semibold tracking-tight">
            Career Portal
          </p>
          <p className="text-slate-400 text-xs mt-0.5">
            University Platform
          </p>
        </div>
      </div>

      {/* Spinner + label */}
      <div className="flex items-center gap-2 text-slate-400 text-xs font-medium animate-fade-in delay-150">
        <Spinner />
        <span>Loading…</span>
      </div>

      {/* Subtle bottom rule — grounds the layout */}
      <div
        className="absolute bottom-0 left-0 right-0 h-0.5"
        style={{
          background:
            "linear-gradient(90deg, transparent 0%, #4f6ef730 40%, #4f6ef750 50%, #4f6ef730 60%, transparent 100%)",
        }}
        aria-hidden="true"
      />

    </div>
  );
}
