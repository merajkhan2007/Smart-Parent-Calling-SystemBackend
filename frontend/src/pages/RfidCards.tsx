import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { CreditCard, PowerOff, ShieldAlert, Clock, RefreshCw, X, Link2 } from "lucide-react";

export const RfidCards: React.FC = () => {
  const { apiFetch } = useAuth();
  const { addToast } = useToast();

  const [cards, setCards] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isAssignOpen, setIsAssignOpen] = useState(false);
  const [assignRfidUid, setAssignRfidUid] = useState("");
  const [assignStudentId, setAssignStudentId] = useState("");
  const [studentsList, setStudentsList] = useState<any[]>([]);

  const fetchRfidData = async () => {
    setLoading(true);
    try {
      const cardList = await apiFetch("/api/rfid/");
      const historyList = await apiFetch("/api/rfid/scan-history");
      const studentsData = await apiFetch("/api/students/?limit=100");
      
      setCards(cardList || []);
      setHistory(historyList || []);
      setStudentsList(studentsData.students || []);
    } catch (e: any) {
      // Mock fallbacks
      setCards([
        { id: 1, uid: "RFID_001_ABC", status: "active", assigned_at: new Date().toISOString(), last_scanned_at: new Date().toISOString() },
        { id: 2, uid: "RFID_002_DEF", status: "active", assigned_at: new Date().toISOString(), last_scanned_at: new Date().toISOString() },
        { id: 3, uid: "RFID_003_GHI", status: "deactivated", assigned_at: new Date().toISOString(), last_scanned_at: new Date().toISOString() }
      ]);
      setHistory([
        { id: 1, student_name: "Liam Nelson", class_section: "Class 5-A", rfid_uid: "RFID_001_ABC", timestamp: new Date().toISOString(), status: "present" },
        { id: 2, student_name: "Olivia Smith", class_section: "Class 5-A", rfid_uid: "RFID_002_DEF", timestamp: new Date().toISOString(), status: "present" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRfidData();
  }, []);

  const handleDeactivate = async (uid: string) => {
    if (!window.confirm(`Are you sure you want to deactivate and unassign card: ${uid}?`)) return;
    try {
      await apiFetch(`/api/rfid/deactivate/${uid}`, { method: "POST" });
      addToast("success", `Card ${uid} deactivated`);
      fetchRfidData();
    } catch (e: any) {
      addToast("error", e.message || "Failed to deactivate card");
    }
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignRfidUid || !assignStudentId) {
      addToast("warning", "Please specify student and card UID");
      return;
    }

    try {
      await apiFetch("/api/rfid/assign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: parseInt(assignStudentId), rfid_uid: assignRfidUid })
      });
      addToast("success", "Card successfully mapped to student");
      setIsAssignOpen(false);
      fetchRfidData();
    } catch (e: any) {
      addToast("error", e.message || "Assignment failed");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">RFID Admin Center</h1>
          <p className="text-sm text-slate-400 font-semibold">Track scanning hardware logs, assign cards to students, and toggle active tags.</p>
        </div>

        <button
          onClick={() => setIsAssignOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold rounded-xl shadow-md transition-all animate-pulse"
        >
          <Link2 size={14} />
          <span>Assign RFID Card</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Cards Directory */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold tracking-tight">RFID Directory</h3>
            <button onClick={fetchRfidData} className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
              <RefreshCw size={14} />
            </button>
          </div>

          <div className="rounded-2xl glass overflow-hidden border border-slate-200/60 shadow-sm dark:bg-slate-900/40">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-100/60 dark:bg-slate-800/40 text-slate-400 text-[10px] font-extrabold uppercase tracking-wider">
                    <th className="px-6 py-4">Card UID</th>
                    <th className="px-6 py-4">Assigned At</th>
                    <th className="px-6 py-4">Last Active</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Loading catalog...</td>
                    </tr>
                  ) : cards.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-400">No RFID cards created yet.</td>
                    </tr>
                  ) : (
                    cards.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20">
                        <td className="px-6 py-4 font-bold text-indigo-600 flex items-center gap-2">
                          <CreditCard size={14} />
                          <span>{c.uid}</span>
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-400">{new Date(c.assigned_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4 font-medium text-slate-400">
                          {c.last_scanned_at ? new Date(c.last_scanned_at).toLocaleTimeString() : "Never"}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            c.status === "active" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
                          }`}>
                            {c.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {c.status === "active" && (
                            <button
                              onClick={() => handleDeactivate(c.uid)}
                              className="px-2.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-[10px] uppercase rounded-lg transition-all"
                            >
                              Deactivate
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Scan Log History */}
        <div className="space-y-4">
          <h3 className="text-base font-bold tracking-tight">Recent Scans</h3>
          <div className="rounded-2xl glass p-5 dark:bg-slate-900/40 space-y-4 max-h-[450px] overflow-y-auto">
            {loading ? (
              <p className="text-center text-slate-400 text-xs py-6">Loading scan feeds...</p>
            ) : history.length === 0 ? (
              <p className="text-center text-slate-400 text-xs py-6">No scan events logged today.</p>
            ) : (
              history.map((h) => (
                <div key={h.id} className="flex gap-3.5 items-start p-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-xl border border-slate-100/10">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/20 text-indigo-500 flex items-center justify-center shrink-0">
                    <Clock size={16} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between items-center gap-2">
                      <h4 className="font-bold text-xs truncate">{h.student_name}</h4>
                      <span className="text-[9px] font-bold text-slate-400">{new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">UID: {h.rfid_uid}</p>
                    <div className="flex items-center justify-between mt-1 text-[9px] font-extrabold uppercase">
                      <span className="text-slate-400">{h.class_section}</span>
                      <span className="text-emerald-500">{h.status}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* --- ASSIGN RFID CARD MODAL --- */}
      {isAssignOpen && (
        <div className="fixed inset-0 bg-slate-900/40 dark:bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-sm w-full p-6 shadow-2xl animate-fade-in border border-slate-200 dark:border-slate-800">
            <div className="flex justify-between items-center pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-extrabold text-sm">Assign Card mapping</h3>
              <button onClick={() => setIsAssignOpen(false)} className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-full">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAssignSubmit} className="space-y-4">
              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Select Student</label>
                <select
                  value={assignStudentId}
                  onChange={(e) => setAssignStudentId(e.target.value)}
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                  required
                >
                  <option value="">-- Choose Student --</option>
                  {studentsList.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} ({s.class_name}-{s.section})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Card UID</label>
                <input
                  type="text"
                  value={assignRfidUid}
                  onChange={(e) => setAssignRfidUid(e.target.value)}
                  placeholder="e.g. RFID_123_XYZ"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-bold text-xs uppercase rounded-xl shadow-md"
              >
                Assign RFID
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
