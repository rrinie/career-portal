/**
 * lib/api.js
 * ----------
 * Central Axios instance for all API calls.
 *
 * Behaviours:
 *  1. baseURL points to FastAPI on port 8002.
 *  2. Request interceptor: reads JWT from localStorage and attaches it as
 *     "Authorization: Bearer <token>" on every outgoing request.
 *  3. Response interceptor: on 401, clears the stored token + user and
 *     redirects to /login — handles both expired tokens and invalid sessions.
 *
 * Field name contract (confirmed from backend Pydantic schemas):
 *  - JobPosting  → PostingID, CompanyID, PositionID, Title, WorkType, Deadline
 *  - JobSeeker   → SeekerID, FirstName, LastName, Email, Phone
 *  - Application → ApplicationID, SeekerID, PostingID, Status, ApplicationDate
 *  - Token       → access_token, token_type
 *  - Login form  → "username" maps to Email (OAuth2PasswordRequestForm)
 */

import axios from "axios";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
export const TOKEN_KEY = "cp_access_token";
export const USER_KEY  = "cp_user";

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------
const api = axios.create({
  baseURL: "http://127.0.0.1:8002",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10_000, // 10 seconds — surface hung requests early in development
});

// ---------------------------------------------------------------------------
// Request interceptor — attach JWT
// ---------------------------------------------------------------------------
api.interceptors.request.use(
  (config) => {
    // localStorage is only available in the browser.
    // During SSR this block is skipped safely.
    if (typeof window !== "undefined") {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response interceptor — handle 401
// ---------------------------------------------------------------------------
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      typeof window !== "undefined" &&
      error.response?.status === 401
    ) {
      // Clear all auth state so the next page load starts clean
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);

      // Avoid redirect loop: only redirect if not already on /login
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

/**
 * loginJobSeeker(email, password)
 *
 * The FastAPI endpoint uses OAuth2PasswordRequestForm, which requires the
 * body as multipart/form-data with fields "username" and "password".
 * "username" is mapped to Email on the backend — this is NOT a mistake.
 */
export async function loginJobSeeker(email, password) {
  const form = new URLSearchParams();
  form.append("username", email);   // FastAPI OAuth2 field name
  form.append("password", password);

  const { data } = await api.post("/auth/jobseeker/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  // data = { access_token: "...", token_type: "bearer" }
  return data;
}

/**
 * loginCompany(email, password)
 * Same OAuth2 form encoding — "username" maps to ContactEmail.
 */
export async function loginCompany(email, password) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const { data } = await api.post("/auth/company/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

// ---------------------------------------------------------------------------
// Token / user storage helpers
// ---------------------------------------------------------------------------
export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser() {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    // raw may be the string "null" during the brief window between the two
    // saveSession() calls in login — JSON.parse("null") === null, handled cleanly.
    if (!raw || raw === "null") return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// API call wrappers — typed by resource
// ---------------------------------------------------------------------------

// --- Job Seeker ---
export const seekerApi = {
  getMe:           ()       => api.get("/jobseekers/me"),
  updateMe:        (data)   => api.patch("/jobseekers/me", data),
  getCV:           ()       => api.get("/jobseekers/me/cv"),
  createCV:        (data)   => api.post("/jobseekers/me/cv", data),
  updateCV:        (data)   => api.patch("/jobseekers/me/cv", data),
  getApplications: ()       => api.get("/jobseekers/me/applications"),
};

// --- Jobs (public board) ---
export const jobsApi = {
  list:    (params) => api.get("/jobs/postings", { params }),
  getOne:  (id)     => api.get(`/jobs/postings/${id}`),
};

// --- Applications ---
export const applicationsApi = {
  submit:       (postingId)              => api.post("/applications", { PostingID: postingId }),
  getOne:       (id)                     => api.get(`/applications/${id}`),
  updateStatus: (id, status)             => api.patch(`/applications/${id}/status`, { Status: status }),
  withdraw:     (id)                     => api.delete(`/applications/${id}`),
};

// --- Video Interviews ---
export const interviewsApi = {
  submit:  (applicationId, packageId, videoUrl) =>
    api.post("/interviews", {
      ApplicationID: applicationId,
      PackageID:     packageId,
      VideoURL:      videoUrl,
    }),
  getOne:              (id)  => api.get(`/interviews/${id}`),
  listForApplication:  (id)  => api.get(`/interviews/application/${id}`),
  delete:              (id)  => api.delete(`/interviews/${id}`),
};

// --- Company (authenticated) ---
export const companyApi = {
  getMe:           ()       => api.get("/companies/me"),
  updateMe:        (data)   => api.patch("/companies/me", data),
  getPostings:     ()       => api.get("/companies/me/postings"),
  createPosting:   (data)   => api.post("/companies/me/postings", data),
  updatePosting:   (id, d)  => api.patch(`/companies/me/postings/${id}`, d),
  deletePosting:   (id)     => api.delete(`/companies/me/postings/${id}`),
  getApplications: (id)     => api.get(`/companies/me/postings/${id}/applications`),
};

export default api;
