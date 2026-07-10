import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Search, UserCheck, Shield, Phone, HelpCircle } from "lucide-react";

export const Parents: React.FC = () => {
  const { apiFetch } = useAuth();
  const { addToast } = useToast();

  const [parents, setParents] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchParents = async () => {
    setLoading(true);
    try {
      const data = await apiFetch(`/api/parents/?query=${search}`);
      setParents(data || []);
    } catch (e: any) {
      // Mock fallback
      setParents([
        { id: 1, father_name: "David Nelson", father_mobile: "+15550100", mother_name: "Emily Nelson", mother_mobile: "+15550101", emergency_contact: "+15550999" },
        { id: 2, father_name: "Michael Smith", father_mobile: "+15550200", mother_name: "Sarah Smith", mother_mobile: "+15550201", emergency_contact: "+15550999" },
        { id: 3, father_name: "James Williams", father_mobile: "+15550300", mother_name: "Emma Williams", mother_mobile: "+15550301", emergency_contact: "+15550999" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParents();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchParents();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Parent Profiles</h1>
        <p className="text-sm text-slate-400 font-semibold">Manage family relationships and dialer configurations.</p>
      </div>

      {/* Search Filter */}
      <div className="rounded-2xl glass p-5 dark:bg-slate-900/40">
        <form onSubmit={handleSearchSubmit} className="flex gap-4">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search size={16} />
            </span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search father, mother name or phone..."
              className="block w-full pl-10 pr-3 py-2.5 bg-white/50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2.5 bg-slate-800 hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-650 text-white font-bold text-sm rounded-xl transition-all"
          >
            Search Contacts
          </button>
        </form>
      </div>

      {/* Grid of Profiles */}
      {loading ? (
        <div className="text-center py-12 text-slate-400 font-semibold text-sm">Loading parent directory...</div>
      ) : parents.length === 0 ? (
        <div className="text-center py-12 text-slate-400 font-semibold text-sm">No parents profiles found.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {parents.map((p) => (
            <div key={p.id} className="rounded-3xl glass p-6 border dark:bg-slate-900/40 relative overflow-hidden shadow-sm">
              <div className="flex items-center gap-3 pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
                <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-indigo-950/20 text-indigo-600 flex items-center justify-center shadow-sm">
                  <UserCheck size={20} />
                </div>
                <div>
                  <h3 className="font-extrabold text-sm text-slate-700 dark:text-slate-200">Family Profile #{p.id}</h3>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Primary Contacts</span>
                </div>
              </div>

              <div className="space-y-3.5 text-xs">
                {/* Father */}
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Father</span>
                    <p className="font-bold text-sm text-slate-700 dark:text-slate-300">{p.father_name || "N/A"}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Mobile</span>
                    <p className="font-semibold text-primary-600 dark:text-primary-400 flex items-center gap-1">
                      <Phone size={10} />
                      <span>{p.father_mobile || "N/A"}</span>
                    </p>
                  </div>
                </div>

                {/* Mother */}
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Mother</span>
                    <p className="font-bold text-sm text-slate-700 dark:text-slate-300">{p.mother_name || "N/A"}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Mobile</span>
                    <p className="font-semibold text-primary-600 dark:text-primary-400 flex items-center gap-1">
                      <Phone size={10} />
                      <span>{p.mother_mobile || "N/A"}</span>
                    </p>
                  </div>
                </div>

                {/* Emergency Contact */}
                <div className="flex justify-between items-center pt-3 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1">
                    <Shield size={10} className="text-rose-500" />
                    <span>Emergency Contact</span>
                  </span>
                  <span className="font-bold text-slate-600 dark:text-slate-300">{p.emergency_contact || p.father_mobile}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
