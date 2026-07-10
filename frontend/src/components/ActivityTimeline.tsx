import React from "react";
import { Phone, CreditCard, PhoneOff, CheckCircle } from "lucide-react";

interface Activity {
  id: string;
  type: string; // call, scan, alert
  time: string;
  title: string;
  subtitle: string;
  tag: string;
}

interface ActivityTimelineProps {
  activities: Activity[];
  loading?: boolean;
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ activities, loading = false }) => {
  if (loading) {
    return (
      <div className="saas-card bg-white dark:bg-slate-900 p-6 shimmer-bg animate-pulse">
        <div className="h-5 bg-slate-100 dark:bg-slate-800 rounded w-36 mb-6"></div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-1/2"></div>
                <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const getIcon = (type: string, tag: string) => {
    if (type === "scan") return { icon: CreditCard, color: "bg-indigo-50 text-indigo-500 border-indigo-100 dark:bg-indigo-950/20 dark:border-indigo-900/30" };
    if (tag === "completed" || tag === "success") return { icon: CheckCircle, color: "bg-emerald-50 text-emerald-500 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900/30" };
    if (tag === "failed" || tag === "rejected" || tag === "error") return { icon: PhoneOff, color: "bg-rose-50 text-rose-500 border-rose-100 dark:bg-rose-950/20 dark:border-rose-900/30" };
    return { icon: Phone, color: "bg-primary-50 text-primary-500 border-primary-100 dark:bg-primary-950/20 dark:border-primary-900/30" };
  };

  return (
    <div className="saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80">
      <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-6 tracking-tight">Today's Activity Timeline</h3>
      
      {activities.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-400 font-medium">No activity recorded today yet.</div>
      ) : (
        <div className="relative border-l border-slate-100 dark:border-slate-800 pl-6 ml-4 space-y-6">
          {activities.map((act) => {
            const { icon: Icon, color } = getIcon(act.type, act.tag);
            return (
              <div key={act.id} className="relative group">
                {/* Bullet indicator */}
                <div className={`absolute -left-[37px] top-0 w-8 h-8 rounded-full border flex items-center justify-center ${color} bg-white dark:bg-slate-900 shadow-sm transition-transform duration-150 group-hover:scale-105 z-10`}>
                  <Icon size={13} />
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <h4 className="font-semibold text-xs text-slate-800 dark:text-slate-200 transition-colors group-hover:text-primary-500">
                    {act.title}
                  </h4>
                  <span className="text-[9px] text-slate-400 font-semibold bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded-md w-max">
                    {act.time}
                  </span>
                </div>
                
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {act.subtitle}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
