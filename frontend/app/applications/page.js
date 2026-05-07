"use client";
import { useState, useEffect } from "react";
import { seekerApi, applicationsApi } from "@/lib/api";
import DashboardLayout from "@/components/DashboardLayout";
import { Calendar, FileText, Trash2 } from "lucide-react";

const STATUS_COLORS = {
  Pending: "bg-yellow-50 text-yellow-800 border-yellow-200",
  Reviewed: "bg-blue-50 text-blue-800 border-blue-200",
  Shortlisted: "bg-green-50 text-green-800 border-green-200",
  Rejected: "bg-red-50 text-red-800 border-red-200",
  Hired: "bg-purple-50 text-purple-800 border-purple-200",
};

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [withdrawing, setWithdrawing] = useState(null);

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const response = await seekerApi.getApplications();
        setApplications(response.data || []);
      } catch (err) {
        console.error("Failed to fetch applications", err);
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, []);

  const handleWithdraw = async (applicationId) => {
    if (!window.confirm("Are you sure you want to withdraw this application?")) {
      return;
    }

    setWithdrawing(applicationId);
    try {
      await applicationsApi.withdraw(applicationId);
      setApplications(applications.filter((app) => app.ApplicationID !== applicationId));
      alert("Application withdrawn successfully.");
    } catch (err) {
      alert("Failed to withdraw application. Please try again.");
    } finally {
      setWithdrawing(null);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="max-w-4xl mx-auto p-6 flex items-center justify-center min-h-96">
          <div className="text-slate-400">Loading applications...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">My Applications</h1>
          <p className="text-slate-500">Track and manage your job applications.</p>
        </header>

        {applications.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No applications yet</h3>
            <p className="text-slate-500">Visit the job board to apply for positions.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {applications.map((app) => (
              <div
                key={app.ApplicationID}
                className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">
                      Application #{app.ApplicationID}
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-500 mb-1">Job Posting</p>
                        <p className="font-medium text-slate-900">Posting #{app.PostingID}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 mb-1">Date Applied</p>
                        <p className="font-medium text-slate-900 flex items-center gap-2">
                          <Calendar size={16} />
                          {new Date(app.ApplicationDate).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <p className="text-slate-500 text-sm mb-2">Status</p>
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${
                          STATUS_COLORS[app.Status] || "bg-slate-50 text-slate-800 border-slate-200"
                        }`}
                      >
                        {app.Status}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleWithdraw(app.ApplicationID)}
                    disabled={withdrawing === app.ApplicationID}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Withdraw application"
                  >
                    <Trash2 size={20} />
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
