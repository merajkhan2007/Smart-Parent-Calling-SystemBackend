import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useWebSocket } from "../context/WebSocketContext";
import {
  LayoutDashboard,
  Users,
  UserCheck,
  CreditCard,
  Cpu,
  PhoneCall,
  BarChart3,
  Bell,
  Settings,
  Shield,
  School,
  LogOut,
  Menu,
  X,
  Sun,
  Moon,
  Volume2,
  Search,
  ChevronDown
} from "lucide-react";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const { isConnected } = useWebSocket();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState<any[]>([
    { id: 1, type: "device_offline", message: "Classroom 5-A Scanner went offline", time: "10 mins ago" },
    { id: 2, type: "sim_balance_low", message: "LTE module reports low SIM balance", time: "1 hour ago" }
  ]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    if (!isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const navItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Students", path: "/students", icon: Users },
    { name: "Parents", path: "/parents", icon: UserCheck },
    { name: "RFID Cards", path: "/rfids", icon: CreditCard },
    { name: "ESP32 Devices", path: "/devices", icon: Cpu },
    { name: "Call History", path: "/calls", icon: PhoneCall },
    { name: "Reports", path: "/reports", icon: BarChart3 },
    { name: "Settings", path: "/settings", icon: Settings },
    { name: "Users", path: "/users", icon: Shield, roleLimit: ["Super Admin", "School Admin"] },
    { name: "School Profile", path: "/school", icon: School, roleLimit: ["Super Admin", "School Admin"] }
  ];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-[#F8FAFC] text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans transition-colors duration-200">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800/80 z-20 transition-all duration-300">
        {/* Brand Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-100 dark:border-slate-800">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center text-white shadow-sm shadow-primary-500/25">
              <Volume2 size={18} />
            </div>
            <div>
              <span className="font-bold text-base text-slate-900 dark:text-white tracking-tight">Oakridge SPCS</span>
              <p className="text-[9px] text-slate-400 font-semibold tracking-wider -mt-0.5">ENTERPRISE DIALER</p>
            </div>
          </Link>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            if (item.roleLimit && (!user || !item.roleLimit.includes(user.role))) return null;
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-all duration-150 ${
                  isActive
                    ? "bg-slate-50 dark:bg-slate-800/50 text-primary-500 dark:text-primary-400 border-l-4 border-primary-500 font-semibold"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
                }`}
              >
                <Icon size={17} className={isActive ? "text-primary-500 dark:text-primary-400" : "text-slate-400"} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom Profile Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-2 px-2">
            <div className="w-8.5 h-8.5 rounded-full bg-primary-100 dark:bg-primary-950/40 flex items-center justify-center text-primary-500 font-bold text-xs">
              {user?.name?.slice(0, 2) || "AD"}
            </div>
            <div className="overflow-hidden flex-1">
              <h4 className="font-semibold text-xs text-slate-800 dark:text-slate-200 truncate">{user?.name || "SPCS User"}</h4>
              <p className="text-[10px] text-slate-400 truncate capitalize">{user?.role || "Staff"}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-rose-500 hover:text-rose-600 font-semibold text-xs transition-colors hover:bg-rose-500/5 cursor-pointer"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Sidebar - Mobile drawer */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 bg-slate-900/30 dark:bg-black/60 backdrop-blur-xs z-50 lg:hidden">
          <aside className="w-72 max-w-[80vw] h-full flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100 dark:border-slate-800">
              <span className="font-bold text-base text-slate-900 dark:text-white">Oakridge SPCS</span>
              <button onClick={() => setIsMobileMenuOpen(false)} className="p-1 text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
              {navItems.map((item) => {
                if (item.roleLimit && (!user || !item.roleLimit.includes(user.role))) return null;
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.name}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-all ${
                      isActive
                        ? "bg-slate-50 dark:bg-slate-800/50 text-primary-500 dark:text-primary-400 border-l-4 border-primary-500 font-semibold"
                        : "text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/30"
                    }`}
                  >
                    <Icon size={17} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="p-4 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-rose-500 hover:text-rose-600 font-semibold text-xs hover:bg-rose-500/5"
              >
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Navbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900 sticky top-0 z-30 transition-all">
          <div className="flex items-center gap-4 flex-1">
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <Menu size={18} />
            </button>

            {/* Premium Search Bar */}
            <div className="relative max-w-md w-full hidden md:block">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search size={15} />
              </div>
              <input
                type="text"
                className="block w-full pl-9 pr-4 py-1.5 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all"
                placeholder="Search students, cards, call logs (Press /)"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 md:gap-4">
            {/* Real-time Hardware Connectivity state */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-50 dark:bg-slate-800/50 text-[10px] font-semibold border border-slate-200/50 dark:border-slate-700/30 rounded-full">
              <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500 animate-ping"}`}></span>
              <span className="text-slate-500 dark:text-slate-400">
                {isConnected ? "LTE Server Connected" : "Reconnecting"}
              </span>
            </div>

            {/* School Profile Indicator */}
            <div className="hidden lg:flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>Oakridge International</span>
            </div>

            {/* Dark Mode toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-800 dark:text-slate-500 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
            >
              {isDarkMode ? <Sun size={17} /> : <Moon size={17} />}
            </button>

            {/* Notifications panel dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-800 dark:text-slate-500 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors relative"
              >
                <Bell size={17} />
                {unreadNotifications.length > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                )}
              </button>

              {isNotificationsOpen && (
                <div className="absolute right-0 mt-3 w-80 rounded-2xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 z-50 p-2">
                  <div className="px-4 py-2.5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                    <span className="font-bold text-xs text-slate-800 dark:text-slate-200">Alerts & Incidents</span>
                    <button
                      onClick={() => setUnreadNotifications([])}
                      className="text-[10px] text-primary-500 hover:text-primary-600 font-semibold"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="max-h-60 overflow-y-auto py-1">
                    {unreadNotifications.length === 0 ? (
                      <p className="text-center py-6 text-xs text-slate-400 font-medium">All systems green.</p>
                    ) : (
                      unreadNotifications.map((n) => (
                        <div
                          key={n.id}
                          className="px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/30 rounded-lg transition-colors mb-0.5 cursor-pointer"
                        >
                          <p className="text-[11px] font-medium text-slate-700 dark:text-slate-300">{n.message}</p>
                          <span className="text-[9px] text-slate-400 mt-0.5 block">{n.time}</span>
                        </div>
                      ))
                    )}
                  </div>
                  <div className="p-1 border-t border-slate-100 dark:border-slate-800">
                    <Link
                      to="/notifications"
                      onClick={() => setIsNotificationsOpen(false)}
                      className="block text-center w-full py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-[10px] font-semibold text-slate-600 dark:text-slate-400 rounded-lg"
                    >
                      View Logs
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Premium Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center gap-1.5 p-1 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <div className="w-7.5 h-7.5 rounded-lg bg-primary-500 text-white font-bold text-[11px] flex items-center justify-center uppercase shadow-sm shadow-primary-500/10">
                  {user?.name?.slice(0, 2) || "AD"}
                </div>
                <ChevronDown size={14} className="text-slate-400" />
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 mt-3 w-48 rounded-xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 z-50 p-1.5">
                  <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800">
                    <h5 className="font-semibold text-xs text-slate-900 dark:text-white truncate">{user?.name || "SPCS User"}</h5>
                    <p className="text-[10px] text-slate-400 truncate">{user?.email || "admin@spcs.com"}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-rose-500 hover:bg-rose-500/5 font-medium text-xs transition-colors mt-1 cursor-pointer"
                  >
                    <LogOut size={13} />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Inner Container with light background */}
        <main className="flex-1 p-6 overflow-y-auto bg-[#F8FAFC] dark:bg-slate-950">
          {children}
        </main>
      </div>
    </div>
  );
};
