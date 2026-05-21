"use client";

/**
 * app/signup/page.js
 * ------------------
 * Job Seeker and Company sign-up page.
 *
 * API calls:
 *   JobSeeker: POST /auth/jobseeker/register
 *   Company:   POST /auth/company/register
 * Payloads use PascalCase to match backend Pydantic schemas.
 * On success: redirects to /login with ?registered=1 so the login page can
 *             show a one-time success banner.
 *
 * Note on file extension: the rest of the project uses .js — this file follows
 * that convention rather than the .tsx mentioned in the spec, so imports and
 * tooling stay consistent with the existing setup.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getApiErrorMessage, isAuthenticated, registerCompany, registerJobSeeker } from "../../lib/api";

// ─── Logo mark — identical to login/page.js ───────────────────────────────────
function LogoMark({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#4f6ef7" />
      <path d="M8 22L14 10L20 18L24 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="24" cy="14" r="2.5" fill="white" />
    </svg>
  );
}

// ─── Spinner — identical to login/page.js ────────────────────────────────────
function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  );
}

// ─── Password strength meter ──────────────────────────────────────────────────
// Returns { score: 0-4, label, colour } so the UI can give live feedback.
function getPasswordStrength(password) {
  if (!password) return { score: 0, label: "", color: "" };
  let score = 0;
  if (password.length >= 8)                        score++;
  if (/[A-Z]/.test(password))                      score++;
  if (/[0-9]/.test(password))                      score++;
  if (/[^A-Za-z0-9]/.test(password))               score++;

  const map = [
    { label: "",          color: "bg-slate-200"  },
    { label: "Weak",      color: "bg-danger"      },
    { label: "Fair",      color: "bg-warning"     },
    { label: "Good",      color: "bg-accent"      },
    { label: "Strong",    color: "bg-success"     },
  ];
  return { score, ...map[score] };
}

// ─── Reusable labelled input ──────────────────────────────────────────────────
function Field({ id, label, type = "text", value, onChange, placeholder, autoComplete, error, hint, children }) {
  return (
    <div>
      <label htmlFor={id} className="form-label">{label}</label>
      <div className="relative">
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={`form-input ${error ? "border-danger focus:!border-danger focus:!shadow-[0_0_0_3px_#ef444430]" : ""}`}
        />
        {children}
      </div>
      {error  && <p className="mt-1 text-xs text-danger">{error}</p>}
      {hint && !error && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

// ─── Eye toggle button (password visibility) ─────────────────────────────────
function EyeToggle({ visible, onToggle }) {
  return (
    <button
      type="button"
      tabIndex={-1}
      onClick={onToggle}
      aria-label={visible ? "Hide password" : "Show password"}
      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
    >
      {visible ? (
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
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function SignupPage() {
  const router = useRouter();

  const [actor, setActor] = useState("seeker");

  // Form state
  const [form, setForm] = useState({
    FirstName: "",
    LastName: "",
    CompanyName: "",
    Industry: "",
    City: "",
    Email: "",
    ContactEmail: "",
    Password: "",
    Confirm: "",
  });

  // UI state
  const [errors,      setErrors]      = useState({});
  const [serverError, setServerError] = useState("");
  const [loading,     setLoading]     = useState(false);
  const [showPass,    setShowPass]    = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const strength = getPasswordStrength(form.Password);

  // Already logged-in users skip to the board
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (isAuthenticated()) router.replace("/jobs");
  }, []);

  // ── Field updater ──────────────────────────────────────────────────────────
  const set = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    // Clear the field-level error as soon as the user starts correcting it
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: "" }));
    if (serverError)   setServerError("");
  };

  // ── Client-side validation ─────────────────────────────────────────────────
  // Mirrors the backend Pydantic rules so the user gets instant feedback
  // before a network round-trip.
  function validate() {
    const e = {};
    const emailField = actor === "seeker" ? "Email" : "ContactEmail";
    const emailValue = form[emailField].trim();

    if (actor === "seeker") {
      if (!form.FirstName.trim())
        e.FirstName = "First name is required.";
      else if (form.FirstName.trim().length > 50)
        e.FirstName = "Max 50 characters.";

      if (!form.LastName.trim())
        e.LastName = "Last name is required.";
      else if (form.LastName.trim().length > 50)
        e.LastName = "Max 50 characters.";
    } else {
      if (!form.CompanyName.trim())
        e.CompanyName = "Company name is required.";
      else if (form.CompanyName.trim().length > 100)
        e.CompanyName = "Max 100 characters.";

      if (form.Industry.trim().length > 50)
        e.Industry = "Max 50 characters.";

      if (form.City.trim().length > 50)
        e.City = "Max 50 characters.";
    }

    if (!emailValue)
      e[emailField] = "Email address is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue))
      e[emailField] = "Enter a valid email address.";

    if (!form.Password)
      e.Password = "Password is required.";
    else if (form.Password.length < 8)
      e.Password = "Password must be at least 8 characters.";
    else if (!/[0-9]/.test(form.Password))
      e.Password = "Password must contain at least one digit.";

    if (!form.Confirm)
      e.Confirm = "Please confirm your password.";
    else if (form.Confirm !== form.Password)
      e.Confirm = "Passwords do not match.";

    return e;
  }

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError("");

    // 1. Client-side validation first — no network call if form is invalid
    const fieldErrors = validate();
    if (Object.keys(fieldErrors).length > 0) {
      setErrors(fieldErrors);
      // Focus the first invalid field
      const first = Object.keys(fieldErrors)[0].toLowerCase();
      document.getElementById(first)?.focus();
      return;
    }

    setLoading(true);
    try {
      if (actor === "seeker") {
        await registerJobSeeker({
          FirstName: form.FirstName.trim(),
          LastName: form.LastName.trim(),
          Email: form.Email.trim(),
          Password: form.Password,
        });
      } else {
        await registerCompany({
          CompanyName: form.CompanyName.trim(),
          Industry: form.Industry.trim() || null,
          City: form.City.trim() || null,
          ContactEmail: form.ContactEmail.trim(),
          Password: form.Password,
        });
      }

      // Success — redirect to login with a flag so it can show a banner
      router.push("/login?registered=1");

    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        // Map known backend messages to the right field
        if (detail.toLowerCase().includes("email")) {
          setErrors({ [actor === "seeker" ? "Email" : "ContactEmail"]: detail });
        } else {
          setServerError(detail);
        }
      } else if (Array.isArray(detail)) {
        // Pydantic validation error array — map each error to its field
        const mapped = {};
        detail.forEach((d) => {
          const field = d.loc?.[1];   // e.g. ["body", "Email"]
          if (field) mapped[field] = d.msg;
          else setServerError((prev) => prev + d.msg + " ");
        });
        setErrors(mapped);
      } else {
        setServerError(getApiErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Derived: is the submit button activatable? ─────────────────────────────
  const canSubmit =
    !loading &&
    (actor === "seeker"
      ? form.FirstName && form.LastName && form.Email
      : form.CompanyName && form.ContactEmail) &&
    form.Password &&
    form.Confirm;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 flex">

      {/* ── Left brand panel — mirrors login/page.js exactly ──────── */}
      <div
        className="hidden lg:flex flex-col justify-between w-[480px] flex-shrink-0 p-12"
        style={{ background: "linear-gradient(145deg, #0f172a 0%, #1a2744 60%, #0f172a 100%)" }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3">
          <LogoMark />
          <span className="text-white font-semibold text-lg tracking-tight">Career Portal</span>
        </div>

        {/* Hero */}
        <div className="animate-fade-up">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-4">
            Join the platform
          </p>
          <h1 className="text-white text-4xl font-bold leading-tight mb-6">
            Your next role<br />starts here.
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
            {actor === "seeker"
              ? "Create your free Job Seeker account to browse open roles, build your CV profile, and submit structured video interviews."
              : "Create a Company account to publish job postings, manage applications, and review structured video interviews."}
          </p>
        </div>

        {/* Step strip */}
        <div className="space-y-3">
          {[
            { n: "01", text: "Create your account"         },
            { n: "02", text: actor === "seeker" ? "Build your CV profile" : "Publish job postings" },
            { n: "03", text: actor === "seeker" ? "Apply and interview online" : "Review applications" },
          ].map(({ n, text }) => (
            <div key={n} className="flex items-center gap-3">
              <span className="text-[11px] font-bold text-accent font-mono w-6 flex-shrink-0">{n}</span>
              <span className="text-slate-400 text-sm">{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right form panel ──────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6 overflow-y-auto">
        <div className="w-full max-w-[420px] py-8 animate-fade-up">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2 mb-8 justify-center">
            <LogoMark />
            <span className="font-semibold text-slate-900 text-lg">Career Portal</span>
          </div>

          {/* Header */}
          <div className="mb-7">
            <h2 className="text-2xl font-bold text-slate-900 mb-1">Create account</h2>
            <p className="text-slate-500 text-sm">
              {actor === "seeker" ? "Job Seeker · free forever" : "Company · hiring workspace"}
            </p>
          </div>

          <div className="flex bg-slate-100 rounded-lg p-1 mb-6">
            {[
              ["seeker", "Job Seeker"],
              ["company", "Company"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => { setActor(value); setErrors({}); setServerError(""); }}
                className={`flex-1 py-2 text-sm font-semibold rounded-md transition-all duration-150 ${
                  actor === value
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Card */}
          <div className="card p-6">
            <form onSubmit={handleSubmit} noValidate>

              {actor === "seeker" ? (
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <Field
                    id="firstname"
                    label="First name"
                    value={form.FirstName}
                    onChange={set("FirstName")}
                    placeholder="Alex"
                    autoComplete="given-name"
                    error={errors.FirstName}
                  />
                  <Field
                    id="lastname"
                    label="Last name"
                    value={form.LastName}
                    onChange={set("LastName")}
                    placeholder="Morgan"
                    autoComplete="family-name"
                    error={errors.LastName}
                  />
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <Field
                      id="companyname"
                      label="Company name"
                      value={form.CompanyName}
                      onChange={set("CompanyName")}
                      placeholder="TechNova"
                      autoComplete="organization"
                      error={errors.CompanyName}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <Field
                      id="industry"
                      label="Industry"
                      value={form.Industry}
                      onChange={set("Industry")}
                      placeholder="Software"
                      autoComplete="organization-title"
                      error={errors.Industry}
                    />
                    <Field
                      id="city"
                      label="City"
                      value={form.City}
                      onChange={set("City")}
                      placeholder="Istanbul"
                      autoComplete="address-level2"
                      error={errors.City}
                    />
                  </div>
                </>
              )}

              {/* Email */}
              <div className="mb-4">
                <Field
                  id="email"
                  label={actor === "seeker" ? "Email address" : "Company email"}
                  type="email"
                  value={actor === "seeker" ? form.Email : form.ContactEmail}
                  onChange={actor === "seeker" ? set("Email") : set("ContactEmail")}
                  placeholder={actor === "seeker" ? "alex.morgan@email.com" : "hr@technova.io"}
                  autoComplete="email"
                  error={actor === "seeker" ? errors.Email : errors.ContactEmail}
                />
              </div>

              {/* Password */}
              <div className="mb-1">
                <Field
                  id="password"
                  label="Password"
                  type={showPass ? "text" : "password"}
                  value={form.Password}
                  onChange={set("Password")}
                  placeholder="Min. 8 characters, at least 1 digit"
                  autoComplete="new-password"
                  error={errors.Password}
                  hint="Min. 8 characters with at least one number."
                >
                  <EyeToggle visible={showPass} onToggle={() => setShowPass(p => !p)} />
                </Field>
              </div>

              {/* Strength meter — only shown once the user starts typing */}
              {form.Password && (
                <div className="mb-4 mt-2">
                  <div className="flex gap-1 mb-1">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                          i <= strength.score ? strength.color : "bg-slate-100"
                        }`}
                      />
                    ))}
                  </div>
                  {strength.label && (
                    <p className="text-[11px] text-slate-400">
                      Strength:{" "}
                      <span className={`font-semibold ${
                        strength.score === 1 ? "text-danger"  :
                        strength.score === 2 ? "text-warning" :
                        strength.score === 3 ? "text-accent"  : "text-success"
                      }`}>
                        {strength.label}
                      </span>
                    </p>
                  )}
                </div>
              )}

              {/* Confirm password */}
              <div className="mb-5">
                <Field
                  id="confirm"
                  label="Confirm password"
                  type={showConfirm ? "text" : "password"}
                  value={form.Confirm}
                  onChange={set("Confirm")}
                  placeholder="Repeat your password"
                  autoComplete="new-password"
                  error={errors.Confirm}
                >
                  <EyeToggle visible={showConfirm} onToggle={() => setShowConfirm(p => !p)} />
                  {/* Inline match indicator */}
                  {form.Confirm && !errors.Confirm && form.Confirm === form.Password && (
                    <span className="absolute right-9 top-1/2 -translate-y-1/2">
                      <svg className="w-4 h-4 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  )}
                </Field>
              </div>

              {/* Server-level error */}
              {serverError && (
                <div className="mb-4 flex items-start gap-2 text-danger text-sm bg-red-50 border border-red-100 rounded-md px-3 py-2 animate-fade-in">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <span>{serverError}</span>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={!canSubmit}
                className="btn-primary w-full justify-center"
              >
                {loading ? <><Spinner /> Creating account…</> : actor === "seeker" ? "Create Job Seeker account" : "Create Company account"}
              </button>

            </form>
          </div>

          {/* Sign-in link */}
          <p className="text-center text-sm text-slate-500 mt-5">
            Already have an account?{" "}
            <Link href="/login" className="text-accent font-semibold hover:underline">
              Sign in
            </Link>
          </p>

        </div>
      </div>
    </div>
  );
}
