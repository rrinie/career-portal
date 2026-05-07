"use client";
import { useState, useEffect } from "react";
import { seekerApi } from "@/lib/api";
import DashboardLayout from "@/components/DashboardLayout";
import { User, Mail, Phone, Award, BookOpen, Link as LinkIcon } from "lucide-react";

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [cv, setCV] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await seekerApi.getMe();
        setProfile(response.data);
        setFormData({
          FirstName: response.data.FirstName || "",
          LastName: response.data.LastName || "",
          Phone: response.data.Phone || "",
        });
        if (response.data.cv_profile) {
          setCV(response.data.cv_profile);
        }
      } catch (err) {
        console.error("Failed to fetch profile", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveProfile = async () => {
    try {
      await seekerApi.updateMe(formData);
      setProfile({ ...profile, ...formData });
      setEditing(false);
      alert("Profile updated successfully!");
    } catch (err) {
      alert("Failed to update profile. Please try again.");
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="max-w-4xl mx-auto p-6 flex items-center justify-center min-h-96">
          <div className="text-slate-400">Loading profile...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
            <p className="text-slate-500">Manage your account information and CV.</p>
          </div>
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Edit Profile
            </button>
          )}
        </header>

        {/* Basic Profile Section */}
        <div className="bg-white rounded-xl border border-slate-200 p-8 mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <User size={20} />
            Personal Information
          </h2>

          {editing ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={formData.FirstName}
                    onChange={(e) => handleInputChange("FirstName", e.target.value)}
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={formData.LastName}
                    onChange={(e) => handleInputChange("LastName", e.target.value)}
                    className="form-input"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={formData.Phone}
                  onChange={(e) => handleInputChange("Phone", e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleSaveProfile}
                  className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                >
                  Save Changes
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="bg-slate-200 text-slate-900 px-6 py-2 rounded-lg font-medium hover:bg-slate-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-8">
              <div>
                <div className="mb-6">
                  <p className="text-slate-500 text-sm mb-1">Full Name</p>
                  <p className="text-lg font-semibold text-slate-900">
                    {profile?.FirstName} {profile?.LastName}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 text-sm mb-1 flex items-center gap-1">
                    <Mail size={16} /> Email
                  </p>
                  <p className="font-medium text-slate-900">{profile?.Email}</p>
                </div>
              </div>
              <div>
                <p className="text-slate-500 text-sm mb-1 flex items-center gap-1">
                  <Phone size={16} /> Phone
                </p>
                <p className="font-medium text-slate-900">{profile?.Phone || "Not provided"}</p>
              </div>
            </div>
          )}
        </div>

        {/* CV Profile Section */}
        {cv ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <BookOpen size={20} />
              CV Profile
            </h2>
            <div className="grid grid-cols-2 gap-8">
              <div>
                <p className="text-slate-500 text-sm mb-1 flex items-center gap-1">
                  <Award size={16} /> Experience
                </p>
                <p className="font-medium text-slate-900">{cv.ExperienceYears} years</p>
              </div>
              <div>
                <p className="text-slate-500 text-sm mb-1">Education Level</p>
                <p className="font-medium text-slate-900">{cv.EducationLevel}</p>
              </div>
              {cv.Summary && (
                <div className="col-span-2">
                  <p className="text-slate-500 text-sm mb-2">Professional Summary</p>
                  <p className="text-slate-900">{cv.Summary}</p>
                </div>
              )}
              {cv.LinkedInURL && (
                <div className="col-span-2">
                  <p className="text-slate-500 text-sm mb-2 flex items-center gap-1">
                    <LinkIcon size={16} /> LinkedIn
                  </p>
                  <a
                    href={cv.LinkedInURL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:text-indigo-700 font-medium"
                  >
                    {cv.LinkedInURL}
                  </a>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No CV Profile</h3>
            <p className="text-slate-500">Create a CV profile to showcase your experience and skills to employers.</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
