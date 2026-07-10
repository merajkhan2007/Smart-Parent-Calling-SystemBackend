import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { School, Upload, FileImage, ShieldCheck } from "lucide-react";

export const SchoolProfile: React.FC = () => {
  const { apiFetch } = useAuth();
  const { addToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [schoolName, setSchoolName] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [contact, setContact] = useState("");
  const [address, setAddress] = useState("");
  const [logoFile, setLogoFile] = useState<File | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/settings/");
      setSchoolName(data.school_name);
      setLogoUrl(data.logo_url || "");
      setContact(data.emergency_contact);
      setAddress("123 Oakridge Street, California, USA");
    } catch (e: any) {
      setSchoolName("Oakridge International High School");
      setLogoUrl("/logo.png");
      setContact("+14155552671");
      setAddress("123 Oakridge Street, California, USA");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleLogoUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!logoFile) return;

    const formData = new FormData();
    formData.append("file", logoFile);

    try {
      const token = localStorage.getItem("spcs_token") || sessionStorage.getItem("spcs_token");
      const res = await fetch("/api/settings/logo", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) throw new Error("Logo upload failed");
      const data = await res.json();
      setLogoUrl(data.logo_url || "");
      addToast("success", "School brand logo uploaded successfully!");
    } catch (err: any) {
      addToast("error", err.message || "Failed to upload logo image");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">School Branding Profile</h1>
        <p className="text-sm text-slate-400 font-semibold">Customize school meta details and dials default banners.</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 font-semibold text-sm">Loading profile...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Card profile summary */}
          <div className="rounded-3xl glass p-6 border dark:bg-slate-900/40 text-center relative overflow-hidden flex flex-col items-center justify-center">
            <div className="w-20 h-20 rounded-3xl bg-indigo-50 dark:bg-indigo-950/20 text-indigo-500 flex items-center justify-center mb-4 border border-indigo-100 shadow-sm shrink-0">
              <School size={36} />
            </div>
            
            <h3 className="font-extrabold text-base">{schoolName}</h3>
            <p className="text-xs text-slate-400 font-bold uppercase mt-1">SPCS Dial-in Node</p>
            
            <div className="w-full mt-6 pt-6 border-t border-slate-100/50 dark:border-slate-800/50 text-left text-xs space-y-3">
              <div className="flex justify-between items-center text-slate-400 font-bold">
                <span>Direct Contact</span>
                <span className="text-slate-700 dark:text-slate-300 font-extrabold">{contact}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400 font-bold">
                <span>Address</span>
                <span className="text-slate-750 dark:text-slate-300 truncate max-w-[150px]">{address}</span>
              </div>
            </div>
          </div>

          {/* Logo brand custom upload */}
          <div className="lg:col-span-2 rounded-3xl glass p-6 border dark:bg-slate-900/40">
            <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100 dark:border-slate-800 mb-6">
              <FileImage size={18} className="text-primary-600" />
              <h3 className="font-extrabold text-sm">Brand Customizations & Logos</h3>
            </div>

            <form onSubmit={handleLogoUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-200 dark:border-slate-800/80 rounded-2xl p-6 text-center">
                <FileImage className="mx-auto text-primary-500 mb-3" size={32} />
                <label className="block text-xs font-bold text-slate-500 mb-2 cursor-pointer">
                  <span>Upload Logo (PNG, JPG, SVG)</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setLogoFile(e.target.files ? e.target.files[0] : null)}
                    className="hidden"
                  />
                </label>
                {logoFile && (
                  <p className="text-xs font-bold text-indigo-600 mt-2">{logoFile.name}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={!logoFile}
                className="w-full py-2.5 bg-slate-800 hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-650 disabled:opacity-50 text-white font-bold text-xs uppercase rounded-xl shadow-md transition-all"
              >
                Save Branding Assets
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
