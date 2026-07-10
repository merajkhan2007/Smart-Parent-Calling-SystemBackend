import React from "react";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color?: string; // bg-primary-500 etc
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
  progress?: number;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  color = "bg-primary-500",
  trend,
  loading = false,
  progress
}) => {
  if (loading) {
    return (
      <div className="saas-card bg-white dark:bg-slate-900 p-6 shadow-sm shimmer-bg animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-20"></div>
          <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800"></div>
        </div>
        <div className="h-8 bg-slate-100 dark:bg-slate-800 rounded w-16 mb-2"></div>
        <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-24"></div>
      </div>
    );
  }

  // Map backend color classes to premium SaaS style
  let iconStyle = "text-primary-500 bg-primary-50 dark:bg-primary-950/40 border border-primary-100/50 dark:border-primary-900/30";
  if (color.includes("emerald") || color.includes("success")) {
    iconStyle = "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-100/50 dark:border-emerald-900/30";
  } else if (color.includes("amber") || color.includes("warning")) {
    iconStyle = "text-amber-500 bg-amber-50 dark:bg-amber-950/40 border border-amber-100/50 dark:border-amber-900/30";
  } else if (color.includes("rose") || color.includes("danger")) {
    iconStyle = "text-rose-500 bg-rose-50 dark:bg-rose-950/40 border border-rose-100/50 dark:border-rose-900/30";
  } else if (color.includes("indigo") || color.includes("blue")) {
    iconStyle = "text-indigo-500 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100/50 dark:border-indigo-900/30";
  }

  return (
    <div className="saas-card bg-white dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80 hover:-translate-y-0.5 transition-all duration-200">
      <div className="flex items-center justify-between mb-4">
        <span className="text-slate-400 dark:text-slate-400 text-xs font-bold uppercase tracking-wider">{title}</span>
        <div className={`w-9.5 h-9.5 rounded-xl ${iconStyle} flex items-center justify-center`}>
          <Icon size={18} />
        </div>
      </div>
      
      <div className="mb-2">
        <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</span>
      </div>
      
      {trend && (
        <div className="flex items-center gap-1.5 text-xs">
          <span className={`font-semibold px-1.5 py-0.5 rounded-md ${
            trend.isPositive 
              ? "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/30" 
              : "text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-950/30"
          }`}>
            {trend.isPositive ? "+" : "-"}{trend.value}%
          </span>
          <span className="text-slate-400 font-medium">from last week</span>
        </div>
      )}

      {progress !== undefined && (
        <div className="mt-4">
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary-500 transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};
