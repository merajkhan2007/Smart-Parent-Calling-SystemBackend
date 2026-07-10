import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Search, Download, Phone, CheckCircle, XCircle, FileSpreadsheet } from "lucide-react";

export const CallHistory: React.FC = () => {
  const { apiFetch } = useAuth();

  const [calls, setCalls] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(15);
  
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchCalls = async () => {
    setLoading(true);
    try {
      const url = `/api/call/?page=${page}&limit=${limit}&student_query=${search}&status=${statusFilter}`;
      const data = await apiFetch(url);
      setCalls(data.calls || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      setCalls([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, [page, statusFilter]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCalls();
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Call Log Transcripts</h1>
          <p className="text-xs text-slate-400 font-semibold">View chronological logs of all calls routed through LTE modules.</p>
        </div>

        <div className="flex gap-2">
          <a
            href="/api/call/export/pdf"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            <Download size={12} />
            <span>Download CSV</span>
          </a>
          <a
            href="/api/call/export/excel"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            <FileSpreadsheet size={12} />
            <span>Download Excel</span>
          </a>
        </div>
      </div>

      {/* Filter panel */}
      <div className="saas-card bg-white dark:bg-slate-900 p-5 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80">
        <form onSubmit={handleFilterSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search size={14} />
            </span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search Student..."
              className="block w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
            >
              <option value="">All Call States</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full py-2 bg-slate-800 hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-650 text-white font-semibold text-xs rounded-lg transition-colors cursor-pointer"
          >
            Filter Logs
          </button>
        </form>
      </div>

      {/* Logs Table */}
      <div className="saas-card bg-white dark:bg-slate-900 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/70 dark:bg-slate-850/50 border-b border-slate-100 dark:border-slate-800 text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                <th className="px-6 py-3.5">Call ID</th>
                <th className="px-6 py-3.5">Student</th>
                <th className="px-6 py-3.5">Parent Called</th>
                <th className="px-6 py-3.5">Phone Number</th>
                <th className="px-6 py-3.5">ESP32 Device</th>
                <th className="px-6 py-3.5">Start Time</th>
                <th className="px-6 py-3.5">Duration</th>
                <th className="px-6 py-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400">Loading call history...</td>
                </tr>
              ) : calls.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400">No call history logs found.</td>
                </tr>
              ) : (
                calls.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                    <td className="px-6 py-3.5 font-semibold text-slate-400">#{c.id}</td>
                    <td className="px-6 py-3.5">
                      <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">{c.student?.name}</span>
                    </td>
                    <td className="px-6 py-3.5 font-semibold text-slate-500 dark:text-slate-400 capitalize">{c.parent_type}</td>
                    <td className="px-6 py-3.5 font-semibold text-primary-500 dark:text-primary-400">
                      <div className="flex items-center gap-1">
                        <Phone size={10} />
                        <span>{c.phone_number}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 font-bold text-slate-500 dark:text-slate-400">{c.device?.name || "Gate A Entrance"}</td>
                    <td className="px-6 py-3.5 text-slate-400 font-semibold">{new Date(c.call_start).toLocaleString()}</td>
                    <td className="px-6 py-3.5 font-semibold text-slate-600 dark:text-slate-350">{c.duration}s</td>
                    <td className="px-6 py-3.5">
                      <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase inline-flex items-center gap-1 border ${
                        c.status === "completed" 
                          ? "bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400" 
                          : "bg-rose-50 text-rose-600 border-rose-100 dark:bg-rose-950/20 dark:text-rose-400"
                      }`}>
                        {c.status === "completed" ? <CheckCircle size={10} /> : <XCircle size={10} />}
                        <span>{c.status}</span>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
