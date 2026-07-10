import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Cpu, RefreshCw, ArrowUpCircle, Wifi, Battery, Signal, Plus, X } from "lucide-react";

export const Devices: React.FC = () => {
  const { apiFetch } = useAuth();
  const { addToast } = useToast();

  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [deviceName, setDeviceName] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [deviceLoc, setDeviceLoc] = useState("");
  const [deviceClassroom, setDeviceClassroom] = useState("");

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/device/");
      setDevices(data || []);
    } catch (e: any) {
      setDevices([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleRestart = async (id: string) => {
    try {
      await apiFetch(`/api/device/restart/${id}`, { method: "POST" });
      addToast("success", `Restart command transmitted to ${id}`);
      fetchDevices();
    } catch (e: any) {
      addToast("error", `Could not trigger restart: ${e.message}`);
    }
  };

  const handleOta = async (id: string) => {
    if (!window.confirm("Do you want to transmit OTA firmware update payload? This might restart the scanner.")) return;
    try {
      await apiFetch(`/api/device/ota/${id}`, { method: "POST" });
      addToast("info", `OTA instruction pushed to ${id}`);
    } catch (e: any) {
      addToast("error", `Firmware transmit failed: ${e.message}`);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deviceName || !deviceId) {
      addToast("warning", "Specify device identifier and name");
      return;
    }

    try {
      await apiFetch("/api/device/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: deviceId,
          name: deviceName,
          location: deviceLoc,
          classroom: deviceClassroom
        })
      });
      addToast("success", "Device successfully registered!");
      setIsRegisterOpen(false);
      setDeviceName("");
      setDeviceId("");
      setDeviceLoc("");
      setDeviceClassroom("");
      fetchDevices();
    } catch (e: any) {
      addToast("error", e.message || "Failed to register device");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">ESP32 Gate Registries</h1>
          <p className="text-xs text-slate-400 font-semibold">Monitor diagnostic telemetry, OTA versions, and restart scanner connections.</p>
        </div>

        <button
          onClick={() => setIsRegisterOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary-500 hover:bg-primary-600 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <Plus size={12} />
          <span>Register Device</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 text-xs font-semibold">Scanning local subnets...</div>
      ) : devices.length === 0 ? (
        <div className="text-center py-12 text-slate-400 text-xs font-semibold">No calling gates registered yet.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map((d) => (
            <div key={d.id} className="saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80 relative overflow-hidden shadow-sm flex flex-col justify-between min-h-[250px]">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8.5 h-8.5 rounded-xl bg-primary-50 dark:bg-primary-950/20 text-primary-600 flex items-center justify-center border border-primary-100 dark:border-primary-900/30">
                      <Cpu size={16} />
                    </div>
                    <div>
                      <h4 className="font-bold text-xs text-slate-800 dark:text-slate-200">{d.name}</h4>
                      <span className="text-[9px] text-slate-400 font-bold uppercase">{d.classroom || "General"}</span>
                    </div>
                  </div>

                  <span className={`px-2.5 py-0.5 rounded-md text-[9px] font-bold uppercase border ${
                    d.status === "online" 
                      ? "bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30 animate-pulse" 
                      : "bg-rose-50 text-rose-600 border-rose-100 dark:bg-rose-950/20 dark:text-rose-400 dark:border-rose-900/30"
                  }`}>
                    {d.status}
                  </span>
                </div>

                <div className="space-y-2 text-[11px] mt-4">
                  <div className="flex justify-between items-center text-slate-400 font-semibold">
                    <span>Device ID</span>
                    <span className="text-slate-700 dark:text-slate-300 font-bold">{d.device_id}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400 font-semibold">
                    <span>IP Address</span>
                    <span className="text-slate-700 dark:text-slate-300 font-bold">{d.ip_address || "N/A"}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400 font-semibold">
                    <span>MAC Address</span>
                    <span className="text-slate-700 dark:text-slate-300 font-bold">{d.mac_address || "N/A"}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400 font-semibold">
                    <span>Firmware version</span>
                    <span className="text-slate-700 dark:text-slate-300 font-bold">{d.firmware_version}</span>
                  </div>
                </div>

                {/* Diagnostics */}
                {d.status === "online" && (
                  <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 text-[10px] text-slate-400 font-semibold">
                    <div className="flex items-center gap-1.5">
                      <Wifi size={12} className="text-slate-400" />
                      <span>{d.wifi_signal} dBm</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Battery size={12} className="text-slate-400" />
                      <span>{d.battery_status}%</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Signal size={12} className="text-slate-400" />
                      <span className="truncate">{d.sim_network || "LTE"}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mt-5">
                <button
                  onClick={() => handleRestart(d.device_id)}
                  disabled={d.status !== "online"}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-750 disabled:opacity-50 text-slate-600 dark:text-slate-300 font-semibold text-xs border border-slate-200 dark:border-slate-850 rounded-lg transition-colors cursor-pointer"
                >
                  <RefreshCw size={11} />
                  <span>Restart</span>
                </button>
                <button
                  onClick={() => handleOta(d.device_id)}
                  disabled={d.status !== "online"}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-primary-50 hover:bg-primary-100 dark:bg-primary-950/20 disabled:opacity-50 text-primary-500 font-semibold text-xs border border-primary-100 rounded-lg transition-colors cursor-pointer"
                >
                  <ArrowUpCircle size={11} />
                  <span>Push OTA</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- REGISTER DEVICE MODAL --- */}
      {isRegisterOpen && (
        <div className="fixed inset-0 bg-slate-900/30 dark:bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800">
            <div className="flex justify-between items-center pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">Register Calling Gate</h3>
              <button onClick={() => setIsRegisterOpen(false)} className="p-1 text-slate-400 hover:bg-slate-550 rounded-full">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Device Serial ID</label>
                <input
                  type="text"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  placeholder="e.g. ESP32_CLASS_7A"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Display Name</label>
                <input
                  type="text"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  placeholder="e.g. Classroom 7-A Gate"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Physical Location</label>
                <input
                  type="text"
                  value={deviceLoc}
                  onChange={(e) => setDeviceLoc(e.target.value)}
                  placeholder="e.g. Block A Floor 2"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Mapped Classroom</label>
                <input
                  type="text"
                  value={deviceClassroom}
                  onChange={(e) => setDeviceClassroom(e.target.value)}
                  placeholder="e.g. Room 204"
                  className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-primary-500 hover:bg-primary-600 text-white font-bold text-xs uppercase rounded-lg shadow-sm transition-colors cursor-pointer"
              >
                Register hardware
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
