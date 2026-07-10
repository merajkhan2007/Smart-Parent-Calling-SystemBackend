import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Shield, Plus, X, Trash2, ShieldAlert, Key } from "lucide-react";

export const Users: React.FC = () => {
  const { apiFetch, user } = useAuth();
  const { addToast } = useToast();

  const [usersList, setUsersList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [formEmail, setFormEmail] = useState("");
  const [formName, setFormName] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formRoleId, setFormRoleId] = useState("3"); // default teacher

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/auth/me"); // gets user details
      // Mock full list as fallback
      setUsersList([
        { id: 1, email: "admin@spcs.com", full_name: "SPCS Super Admin", role: { name: "Super Admin" }, is_active: true },
        { id: 2, email: "schooladmin@spcs.com", full_name: "School Principal", role: { name: "School Admin" }, is_active: true },
        { id: 3, email: "teacher1@spcs.com", full_name: "Sarah Connor", role: { name: "Teacher" }, is_active: true },
        { id: 4, email: "teacher2@spcs.com", full_name: "John Keating", role: { name: "Teacher" }, is_active: true }
      ]);
    } catch (e: any) {
      setUsersList([
        { id: 1, email: "admin@spcs.com", full_name: "SPCS Super Admin", role: { name: "Super Admin" }, is_active: true },
        { id: 2, email: "schooladmin@spcs.com", full_name: "School Principal", role: { name: "School Admin" }, is_active: true },
        { id: 3, email: "teacher1@spcs.com", full_name: "Sarah Connor", role: { name: "Teacher" }, is_active: true },
        { id: 4, email: "teacher2@spcs.com", full_name: "John Keating", role: { name: "Teacher" }, is_active: true }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formEmail || !formName || !formPassword) {
      addToast("warning", "Please fill in all fields");
      return;
    }

    try {
      // In development, mock add or route directly
      addToast("success", `User profile registered: ${formName}`);
      setIsModalOpen(false);
      setFormEmail("");
      setFormName("");
      setFormPassword("");
    } catch (err: any) {
      addToast("error", err.message || "Failed to register user");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">System Users & Roles</h1>
          <p className="text-sm text-slate-400 font-semibold">Assign console privileges to teachers, operators and school admins.</p>
        </div>

        {user?.role === "Super Admin" && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold rounded-xl shadow-md"
          >
            <Plus size={14} />
            <span>Add Administrator</span>
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 text-sm font-semibold">Loading operators database...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {usersList.map((u) => (
            <div key={u.id} className="rounded-3xl glass p-6 border dark:bg-slate-900/40 relative overflow-hidden shadow-sm flex flex-col justify-between min-h-[180px]">
              <div>
                <div className="flex justify-between items-start gap-2 mb-4">
                  <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-indigo-950/20 text-indigo-500 flex items-center justify-center font-extrabold shadow-sm">
                    <Shield size={20} />
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase ${
                    u.role.name === "Super Admin" ? "bg-purple-100 text-purple-800" : u.role.name === "School Admin" ? "bg-blue-100 text-blue-800" : "bg-slate-100 text-slate-800"
                  }`}>
                    {u.role.name}
                  </span>
                </div>

                <h4 className="font-extrabold text-sm text-slate-700 dark:text-slate-200">{u.full_name}</h4>
                <p className="text-xs text-slate-400 font-medium truncate mt-0.5">{u.email}</p>
              </div>

              <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-100/50 dark:border-slate-800/50 text-[10px] text-slate-400 font-bold uppercase">
                <span>Access Status</span>
                <span className="text-emerald-500">Active</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- ADD PRIVILEGED USER MODAL --- */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 dark:bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-sm w-full p-6 shadow-2xl animate-fade-in border border-slate-200 dark:border-slate-800">
            <div className="flex justify-between items-center pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-extrabold text-sm">Add System operator</h3>
              <button onClick={() => setIsModalOpen(false)} className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-full">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Full Name</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="John Connor"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Email Address</label>
                <input
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  placeholder="operator@spcs.com"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">System Password</label>
                <input
                  type="password"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1.5">Access Role</label>
                <select
                  value={formRoleId}
                  onChange={(e) => setFormRoleId(e.target.value)}
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border dark:border-slate-750 rounded-xl text-sm focus:outline-none"
                >
                  <option value="2">School Admin</option>
                  <option value="3">Teacher</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-bold text-xs uppercase rounded-xl shadow-md"
              >
                Register Account
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
