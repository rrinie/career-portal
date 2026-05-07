"use client";
import { useState, useEffect } from 'react';
import { applicationsApi } from '@/lib/api';
import DashboardLayout from '@/components/DashboardLayout';
import { Briefcase, MapPin, Clock } from 'lucide-react';

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [applyingId, setApplyingId] = useState(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8002/jobs/postings');
        const data = await response.json();
        setJobs(data);
      } catch (err) {
        console.error("Failed to fetch jobs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  const handleApply = async (postingId) => {
    setApplyingId(postingId);
    try {
      await applicationsApi.submit(postingId);
      alert("Application submitted successfully!");
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to submit application.";
      alert(errorMsg);
    } finally {
      setApplyingId(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">Available Opportunities</h1>
          <p className="text-slate-500">Explore roles at Abdullah Gül University partner companies.</p>
        </header>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-white rounded-xl border border-slate-200 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <div key={job.PostingID} className="bg-white p-6 rounded-xl border border-slate-200 hover:border-indigo-500 transition-colors shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">{job.Title}</h2>
                    <div className="flex gap-4 mt-2 text-sm text-slate-500">
                      <span className="flex items-center gap-1"><Briefcase size={16}/> {job.WorkType}</span>
                      <span className="flex items-center gap-1"><MapPin size={16}/> {job.Location || 'Remote'}</span>
                      <span className="flex items-center gap-1"><Clock size={16}/> {job.Deadline}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleApply(job.PostingID)}
                    disabled={applyingId !== null}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {applyingId === job.PostingID ? "Applying..." : "Apply Now"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}