import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Bell, Check, X, ShieldAlert, Cpu, AlertTriangle, AlertCircle } from "lucide-react";

export const Notifications: React.FC = () => {
  const { apiFetch } = useAuth();
  const { addToast } = useToast();

  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/notifications/");
      setNotifications(data || []);
    } catch (e: any) {
      // Mock notifications fallbacks
      setNotifications([
        { id: 1, type: "device_offline", message: "Classroom 5-A Scanner went offline: connection lost", is_read: false, created_at: new Date().toISOString() },
        { id: 2, type: "sim_balance_low", message: "LTE Module A7672S at Entrance Gate A reports low SIM card balance (< $2.00)", is_read: false, created_at: new Date().toISOString() },
        { id: 3, type: "call_failed", message: "Call to Mother of Liam Nelson failed. Reason: busy", is_read: true, created_at: new Date().toISOString() },
        { id: 4, type: "rfid_error", message: "Unknown RFID card scanned: UID RFID_999_UNK at Entrance Gate A", is_read: true, created_at: new Date().toISOString() }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await apiFetch("/api/notifications/mark-all-read", { method: "POST" });
      addToast("success", "All alerts marked as read");
      fetchNotifications();
    } catch (e: any) {
      addToast("error", "Could not clear alerts");
    }
  };

  const handleMarkSingleRead = async (id: number) => {
    try {
      await apiFetch(`/api/notifications/${id}/read`, { method: "POST" });
      addToast("success", "Alert marked as read");
      fetchNotifications();
    } catch (e: any) {
      addToast("error", "Failed to resolve alert");
    }
  };

  const getAlertStyle = (type: string) => {
    switch (type) {
      case "device_offline":
        return { icon: Cpu, color: "text-rose-500 bg-rose-50 dark:bg-rose-950/20" };
      case "sim_balance_low":
        return { icon: AlertTriangle, color: "text-amber-500 bg-amber-50 dark:bg-amber-950/20" };
      case "student_blocked":
        return { icon: ShieldAlert, color: "text-rose-600 bg-rose-50 dark:bg-rose-950/20" };
      case "call_failed":
        return { icon: AlertCircle, color: "text-rose-500 bg-rose-50 dark:bg-rose-950/20" };
      default:
        return { icon: Bell, color: "text-indigo-500 bg-indigo-50 dark:bg-indigo-950/20" };
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">System Alerts Center</h1>
          <p className="text-sm text-slate-400 font-semibold">Monitor hardware faults, SIM networks, call errors, and RFID block events.</p>
        </div>

        <button
          onClick={handleMarkAllRead}
          className="flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-xs font-bold rounded-xl transition-all"
        >
          <Check size={14} />
          <span>Mark All Cleared</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 font-semibold text-sm">Querying active alerts...</div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-12 text-slate-400 font-semibold text-sm">No active warnings registered. All systems green.</div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notif) => {
            const { icon: Icon, color } = getAlertStyle(notif.type);
            return (
              <div
                key={notif.id}
                className={`rounded-2xl glass p-5 border flex items-start justify-between gap-4 transition-all duration-350 ${
                  notif.is_read ? "opacity-60 bg-white/20" : "bg-white/40 shadow-sm border-white/30"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shadow-sm shrink-0 ${color}`}>
                    <Icon size={20} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200 leading-snug">{notif.message}</h4>
                    <span className="text-[10px] text-slate-400 font-semibold mt-2 block">
                      {new Date(notif.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                {!notif.is_read && (
                  <button
                    onClick={() => handleMarkSingleRead(notif.id)}
                    title="Mark resolved"
                    className="p-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-500 rounded-lg hover:text-slate-800 transition-all shrink-0"
                  >
                    <Check size={14} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
