import { useState, useEffect } from "react";
import api from "../api";
import { Power } from "lucide-react";

export default function Header() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = async () => {
    try {
      const data = await api.getStatus();
      setStatus(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 10000); // Check every 10s
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    try {
      await api.startSession();
      await loadStatus();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await api.stopSession();
      await loadStatus();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  // Determine active session
  let activeAccount = null;
  if (status && status.kaggle_accounts) {
    activeAccount = status.kaggle_accounts.find(a => a.is_active === 1);
  }

  return (
    <header className="h-16 border-b border-gray-800/50 glass-dark flex items-center justify-between px-8 sticky top-0 z-40">
      <div className="flex items-center gap-2">
        {/* Placeholder for left side if needed */}
        <span className="text-gray-400 font-medium">Dashboard Overview</span>
      </div>

      <div className="flex items-center gap-4">
        {activeAccount ? (
          <div className="flex items-center gap-3 bg-green-500/10 border border-green-500/20 px-4 py-1.5 rounded-full">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
            </span>
            <span className="text-sm font-medium text-green-400">
              Online ({activeAccount.username})
            </span>
            <div className="w-px h-4 bg-green-500/30 mx-1"></div>
            <button 
              onClick={handleStop}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs font-bold text-red-400 hover:text-red-300 transition disabled:opacity-50"
            >
              <Power size={14} /> STOP SESSION
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 bg-gray-800/50 border border-gray-700/50 px-4 py-1.5 rounded-full">
            <span className="relative flex h-2.5 w-2.5">
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
            </span>
            <span className="text-sm font-medium text-gray-400">
              Session Offline
            </span>
            <div className="w-px h-4 bg-gray-700 mx-1"></div>
            <button 
              onClick={handleStart}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs font-bold text-green-400 hover:text-green-300 transition disabled:opacity-50"
            >
              <Power size={14} /> START SESSION
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
