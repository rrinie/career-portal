"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  loginJobSeeker,
  loginCompany,
  saveSession,
  seekerApi,
  companyApi,
  isAuthenticated,
  getApiErrorMessage,
} from "../../lib/api";

// ─── Minimal SVG logo mark ────────────────────────────────────────────────────
function LogoMark() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#4f6ef7" />
      <path d="M8 22L14 10L20 18L24 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="24" cy="14" r="2.5" fill="white" />
    </svg>
  );
}

// ─── Spinner ──────────────────────────────────────────────────────────────────
function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  );
}

// ─── Actor tab ────────────────────────────────────────────────────────────────
function ActorTab({ label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 py-2 text-sm font-semibold rounded-md transition-all duration-150 ${
        active
          ? "bg-white text-slate-900 shadow-sm"
          : "text-slate-500 hover:text-slate-700"
      }`}
    >
      {label}
    </button>
  );
}

// ─── Main Login Page ──────────────────────────────────────────────────────────
export default function LoginPage() {
  const router = useRouter();

  const [actor,    setActor]    = useState("seeker");   // "seeker" | "company"
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const [showPass, setShowPass] = useState(false);
  const searchParams = useSearchParams();
  const justRegistered = searchParams.get("registered") === "1";

  // If already authenticated, skip to the board.
  // Empty dep array = runs once on mount only.
  // router is intentionally omitted: its reference changes every render in
  // Next.js App Router, which would re-trigger this effect mid-navigation
  // and produce a false redirect back to /login.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (isAuthenticated()) router.replace("/jobs");
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // 1. Login — get token
      const loginFn = actor === "seeker" ? loginJobSeeker : loginCompany;
      const tokenData = await loginFn(email, password);
      // tokenData = { access_token: "...", token_type: "bearer" }

      // 2. Save the token first so the /me request can attach it to its header.
      //    We use saveSession with a placeholder user so TOKEN_KEY is always
      //    used consistently — no raw string literals anywhere.
      saveSession(tokenData.access_token, null);

      // 3. Fetch the full profile now that the token is in storage
      const profileRes = actor === "seeker"
        ? await seekerApi.getMe()
        : await companyApi.getMe();

      // 4. Overwrite with the complete user object
      saveSession(tokenData.access_token, {
        ...profileRes.data,
        actorType: actor,
      });

      // 5. Navigate — token + user are fully written before this line
      router.push("/jobs");

    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Fill seed credentials for quick testing
  const fillDemo = () => {
    if (actor === "seeker") {
      setEmail("alex.morgan@email.com");
      setPassword("Password1");
    } else {
      setEmail("hr@technova.io");
      setPassword("Company11");
    }
    setError("");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">

      {/* ── Left panel — brand/illustration ───────────────────────── */}
      <div
        className="hidden lg:flex flex-col justify-between w-[480px] flex-shrink-0 p-12"
        style={{
          background: "linear-gradient(145deg, #0f172a 0%, #1a2744 60%, #0f172a 100%)",
        }}
      >
        {/* Top: logo */}
        <div className="flex items-center gap-3">
          <LogoMark />
          <span className="text-white font-semibold text-lg tracking-tight">
            Career Portal
          </span>
        </div>

        {/* Middle: hero copy */}
        <div className="animate-fade-up">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-4">
            University Recruitment Platform
          </p>
          <h1 className="text-white text-4xl font-bold leading-tight mb-6">
            Connect talent<br />
            with opportunity.
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
            A unified platform for students to discover roles and for
            companies to run structured video interviews — all in one place.
          </p>
        </div>

        {/* Bottom: stat strip */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { n: "43",   label: "API endpoints" },
            { n: "10",   label: "Database tables" },
            { n: "100%", label: "JWT secured" },
          ].map(({ n, label }) => (
            <div key={label} className="border border-slate-700 rounded-lg p-4">
              <div className="text-white font-bold text-xl mb-0.5">{n}</div>
              <div className="text-slate-500 text-xs">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right panel — form ────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-[400px] animate-fade-up">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2 mb-8 justify-center">
            <LogoMark />
            <span className="font-semibold text-slate-900 text-lg">Career Portal</span>
          </div>

          {/* Header */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-1">
              Sign in
            </h2>
            <p className="text-slate-500 text-sm">
              {actor === "seeker"
                ? "Access your job applications and interviews."
                : "Manage your postings and review candidates."}
            </p>
          </div>

          {/* Registration success banner */}
          {justRegistered && (
            <div className="mb-5 flex items-start gap-2.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg px-4 py-3 text-sm animate-fade-in">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="font-semibold">Account created!</p>
                <p className="text-emerald-700 text-xs mt-0.5">Sign in below to access your dashboard.</p>
              </div>
            </div>
          )}

          {/* Actor toggle */}
          <div className="flex bg-slate-100 rounded-lg p-1 mb-6">
            <ActorTab
              label="Job Seeker"
              active={actor === "seeker"}
              onClick={() => { setActor("seeker"); setError(""); }}
            />
            <ActorTab
              label="Company"
              active={actor === "company"}
              onClick={() => { setActor("company"); setError(""); }}
            />
          </div>

          {/* Form card */}
          <div className="card p-6">
            <form onSubmit={handleSubmit} noValidate>

              {/* Email */}
              <div className="mb-4">
                <label htmlFor="email" className="form-label">
                  {actor === "seeker" ? "Email address" : "Company email"}
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={actor === "seeker" ? "alex.morgan@email.com" : "hr@technova.io"}
                  className="form-input"
                />
              </div>

              {/* Password */}
              <div className="mb-2">
                <label htmlFor="password" className="form-label">Password</label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPass ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="form-input pr-10"
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowPass((p) => !p)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                    aria-label={showPass ? "Hide password" : "Show password"}
                  >
                    {showPass ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Error message */}
              {error && (
                <div className="mt-3 mb-1 flex items-start gap-2 text-danger text-sm bg-red-50 border border-red-100 rounded-md px-3 py-2 animate-fade-in">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || !email || !password}
                className="btn-primary w-full justify-center mt-5"
              >
                {loading ? <><Spinner /> Signing in…</> : "Sign in"}
              </button>
            </form>
          </div>

          {/* Demo credentials helper */}
          <div className="mt-4 p-3 bg-slate-100 rounded-lg border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-0.5">
                  Seed credentials
                </p>
                <p className="text-xs text-slate-500 font-mono">
                  {actor === "seeker"
                    ? "alex.morgan@email.com · Password1"
                    : "hr@technova.io · Company11"}
                </p>
              </div>
              <button
                type="button"
                onClick={fillDemo}
                className="btn-ghost text-xs py-1.5 px-3 flex-shrink-0 ml-3"
              >
                Fill
              </button>
            </div>
          </div>

          {/* Switch actor hint */}
          <p className="text-center text-xs text-slate-400 mt-4">
            {actor === "seeker"
              ? <>Recruiting?{" "}<button type="button" onClick={() => setActor("company")} className="text-accent font-medium hover:underline">Sign in as a Company</button></>
              : <>Looking for work?{" "}<button type="button" onClick={() => setActor("seeker")} className="text-accent font-medium hover:underline">Sign in as a Job Seeker</button></>
            }
          </p>

          <p className="text-center text-sm text-slate-500 mt-2">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-accent font-semibold hover:underline">
              Sign up
            </Link>
          </p>

        </div>
      </div>
    </div>
  );
}
