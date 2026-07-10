import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

export const Reports: React.FC = () => {
  const { apiFetch } = useAuth();
  const [loading, setLoading] = useState(true);
  const [callStats, setCallStats] = useState<any>({
    daily_calls: [],
    weekly_calls: [],
    monthly_calls: [],
    status_distribution: [],
    most_active_students: [],
    call_duration_average: 0
  });
  const [, setDeviceStats] = useState<any[]>([]);
  const [parentStats, setParentStats] = useState<any>({
    father_calls: 0,
    mother_calls: 0,
    guardian_calls: 0,
    percentages: { father: 0, mother: 0, guardian: 0 }
  });

  const fetchReportData = async () => {
    setLoading(true);
    try {
      const cStats = await apiFetch("/api/reports/call-statistics");
      const dStats = await apiFetch("/api/reports/device-statistics");
      const pStats = await apiFetch("/api/reports/parent-contact-statistics");
      
      setCallStats(cStats);
      setDeviceStats(dStats);
      setParentStats(pStats);
    } catch (e: any) {
      setCallStats({
        daily_calls: [],
        status_distribution: [],
        most_active_students: [],
        call_duration_average: 0
      });
      setDeviceStats([]);
      setParentStats({
        father_calls: 0,
        mother_calls: 0,
        guardian_calls: 0,
        percentages: { father: 0, mother: 0, guardian: 0 }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, []);

  return (
    <div className="space-y-6 font-sans">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">System Performance Reports</h1>
        <p className="text-xs text-slate-400 font-semibold">Analyze call routing metrics, average call durations, and ESP32 hardware logs.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calling traffic spike chart */}
        <div className="lg:col-span-2 saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80 min-h-[350px] flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold tracking-tight text-slate-800 dark:text-slate-100">Call Volume (Daily Traffic)</h3>
            <p className="text-xs text-slate-400">Total parent calls placed per day</p>
          </div>

          <div className="flex-1 flex items-end justify-between h-48 gap-3 pt-6 border-b border-slate-100 dark:border-slate-800">
            {callStats.daily_calls.map((col: any, idx: number) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                <div 
                  className="w-full bg-primary-500 hover:bg-primary-600 rounded-t-md transition-all duration-200 relative"
                  style={{ height: `${(col.value / 30) * 100}%`, minHeight: "4px" }}
                >
                  <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-[9px] bg-slate-900 text-white rounded px-1.5 py-0.5 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 font-semibold shadow-sm">
                    Calls: {col.value}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-semibold select-none">{col.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Status distribution circular representation */}
        <div className="saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold tracking-tight text-slate-800 dark:text-slate-100">Call Success Ratio</h3>
            <p className="text-xs text-slate-400">Distribution of routed call outcomes</p>
          </div>

          <div className="py-6 flex justify-center items-center">
            <div className="space-y-3.5 w-full">
              {callStats.status_distribution.map((dist: any, i: number) => {
                const colors = {
                  completed: "bg-emerald-500",
                  failed: "bg-rose-500",
                  rejected: "bg-amber-500"
                }[dist.label] || "bg-slate-400";
                
                return (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="capitalize text-slate-700 dark:text-slate-300">{dist.label}</span>
                      <span className="text-slate-500">{dist.value} calls</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-855 h-1.5 rounded-full overflow-hidden">
                      <div className={`h-full ${colors}`} style={{ width: `${(dist.value / 60) * 100}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Parent ratios */}
        <div className="saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-4 tracking-tight">Parent Call Ratio</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span>Father Dialed ({parentStats.father_calls} calls)</span>
              <span className="text-primary-500 font-bold">{parentStats.percentages?.father}%</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="h-full bg-primary-500" style={{ width: `${parentStats.percentages?.father}%` }}></div>
            </div>

            <div className="flex justify-between items-center text-xs font-semibold">
              <span>Mother Dialed ({parentStats.mother_calls} calls)</span>
              <span className="text-indigo-500 font-bold">{parentStats.percentages?.mother}%</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500" style={{ width: `${parentStats.percentages?.mother}%` }}></div>
            </div>
            
            <div className="flex justify-between items-center text-xs font-semibold">
              <span>Guardian Dialed ({parentStats.guardian_calls} calls)</span>
              <span className="text-slate-500 font-bold">{parentStats.percentages?.guardian}%</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="h-full bg-slate-400" style={{ width: `${parentStats.percentages?.guardian}%` }}></div>
            </div>
          </div>
        </div>

        {/* Top Active students */}
        <div className="saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-4 tracking-tight">Most Active Students</h3>
          <div className="space-y-4">
            {callStats.most_active_students.map((stud: any, i: number) => (
              <div key={i} className="flex justify-between items-center p-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-xl border border-slate-100 dark:border-slate-850">
                <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">{stud.student_name}</span>
                <span className="px-2.5 py-1 bg-primary-50 dark:bg-primary-950/20 text-primary-600 dark:text-primary-400 font-bold text-xs rounded-lg border border-primary-100 dark:border-primary-900/30 shadow-2xs">
                  {stud.calls_count} Dial triggers
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
