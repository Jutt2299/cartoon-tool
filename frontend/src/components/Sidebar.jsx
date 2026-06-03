import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, History, Settings, Activity } from "lucide-react";

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: "/", name: "Studio", icon: LayoutDashboard },
    { path: "/history", name: "History", icon: History },
    { path: "/settings", name: "Settings", icon: Settings },
    { path: "/status", name: "Status", icon: Activity },
  ];

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 glass-dark border-r border-gray-800/50 p-6 flex flex-col z-50">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 rounded-xl overflow-hidden shadow-lg shadow-primary-500/30 flex-shrink-0">
          <img src="/favicon.png" alt="Logo" className="w-full h-full object-cover" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Cartoon<span className="text-primary-500">AI</span>
        </h1>
      </div>

      <nav className="flex-1 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive
                  ? "bg-primary-500/10 text-primary-400 font-medium border border-primary-500/20"
                  : "text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent"
              }`}
            >
              <Icon size={20} className={isActive ? "text-primary-500" : "text-gray-500"} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-6 border-t border-gray-800/50">
        <div className="text-xs text-gray-500">
          © 2026 CartoonAI
        </div>
      </div>
    </aside>
  );
}
