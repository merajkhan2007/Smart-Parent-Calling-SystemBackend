import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Settings as SettingsIcon, Clock, Phone, Key, ShieldAlert } from "lucide-react";

export const Settings: React.FC = () => {
  const { apiFetch } = useAuth();
  const { addToast } = useToast();

  const [loading, setLoading] = useState(true);
  
  const [schoolName, setSchoolName] = useState("");
  const [workingStart, setWorkingStart] = useState("");
  const [workingEnd, setWorkingEnd] = useState("");
  const [maxCalls, setMaxCalls] = useState(3);
  const [maxDuration, setMaxDuration] = useState(180);
  const [emergencyContact, setEmergencyContact] = useState("");
  const [allowedStart, setAllowedStart] = useState("");
  const [allowedEnd, setAllowedEnd] = useState("");
  
  const [espApiKey, setEspApiKey] = useState("esp32_secret_api_key_for_secure_device_access");

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/settings/");
      setSchoolName(data.school_name);
      setWorkingStart(data.working_hours_start);
      setWorkingEnd(data.working_hours_end);
      setMaxCalls(data.max_calls_per_day);
      setMaxDuration(data.max_call_duration);
      setEmergencyContact(data.emergency_contact);
      setAllowedStart(data.allowed_calling_time_start);
      setAllowedEnd(data.allowed_calling_time_end);
    } catch (e: any) {
      // Mock configs
      setSchoolName("Oakridge International High School");
      setWorkingStart("08:00");
      setWorkingEnd("16:30");
      setMaxCalls(3);
      setMaxDuration(120);
      setEmergencyContact("+14155552671");
      setAllowedStart("08:00");
      setAllowedEnd("16:00");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/api/settings/", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          school_name: schoolName,
          working_hours_start: workingStart,
          working_hours_end: workingEnd,
          max_calls_per_day: maxCalls,
          max_call_duration: maxDuration,
          emergency_contact: emergencyContact,
          allowed_calling_time_start: allowedStart,
          allowed_calling_time_end: allowedEnd
        })
      });
      addToast("success", "System configuration values updated successfully!");
    } catch (err: any) {
      addToast("error", err.message || "Failed to update settings");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Calling Gate Configuration</h1>
        <p className="text-sm text-slate-400 font-semibold">Adjust permitted dialing window limits, maximum calls limits and security API keys.</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 font-semibold text-sm">Loading config values...</div>
      ) : (
        <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* General Calling Limits */}
            <div className="rounded-3xl glass p-6 border dark:bg-slate-900/40 space-y-4">
              <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100 dark:border-slate-800">
                <SettingsIcon size={18} className="text-primary-600" />
                <h3 className="font-extrabold text-sm">Hardware & Dial Limits</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Max Calls Per Student / Day</label>
                  <input
                    type="number"
                    value={maxCalls}
                    onChange={(e) => setMaxCalls(parseInt(e.target.value))}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Max Call Duration (Seconds)</label>
                  <input
                    type="number"
                    value={maxDuration}
                    onChange={(e) => setMaxDuration(parseInt(e.target.value))}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Allowed Calling Start Time</label>
                  <input
                    type="time"
                    value={allowedStart}
                    onChange={(e) => setAllowedStart(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Allowed Calling End Time</label>
                  <input
                    type="time"
                    value={allowedEnd}
                    onChange={(e) => setAllowedEnd(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                    required
                  />
                </div>
              </div>
            </div>

            {/* School Profile and School Hours */}
            <div className="rounded-3xl glass p-6 border dark:bg-slate-900/40 space-y-4">
              <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100 dark:border-slate-800">
                <Clock size={18} className="text-primary-600" />
                <h3 className="font-extrabold text-sm">School Working Hours</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Working Hours Start</label>
                  <input
                    type="time"
                    value={workingStart}
                    onChange={(e) => setWorkingStart(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Working Hours End</label>
                  <input
                    type="time"
                    value={workingEnd}
                    onChange={(e) => setWorkingEnd(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* System Security Credentials */}
            <div className="rounded-3xl glass p-6 border dark:bg-slate-900/40 space-y-4">
              <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100 dark:border-slate-800">
                <Key size={18} className="text-amber-500" />
                <h3 className="font-extrabold text-sm">Security API Keys</h3>
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">ESP32 Integration API Key</label>
                <input
                  type="text"
                  value={espApiKey}
                  onChange={(e) => setEspApiKey(e.target.value)}
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-xs font-mono text-slate-500 focus:outline-none"
                  disabled
                />
                <p className="text-[10px] text-slate-400 mt-2">
                  This key must match the `ESP32_API_KEY` defined inside ESP32 custom firmwares.
                </p>
              </div>
            </div>

            {/* Save trigger */}
            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-primary-500 to-indigo-500 hover:from-primary-600 hover:to-indigo-650 text-white font-bold text-sm rounded-xl shadow-lg shadow-primary-500/10 transition-all"
            >
              Apply Configurations
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
