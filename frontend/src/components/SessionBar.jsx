import { useState, useEffect } from "react";
import api from "../api";

export default function SessionBar() {
  const [status, setStatus] = useState("offline");
  const [activeAccount, setActiveAccount] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkStatus();
    // Har 10 sec mein status check karo taakay jaldi update ho
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const data = await api.getStatus();
      const active = data.kaggle_accounts.find(a => a.is_active);
      if (active) {
        if (active.ngrok_url) {
          setStatus("online");
        } else {
          setStatus("starting");
        }
        setActiveAccount(active);
      } else {
        setStatus("offline");
        setActiveAccount(null);
      }
    } catch (err) {
      setStatus("offline");
    }
  };

  const startSession = async () => {
    setLoading(true);
    try {
      await api.startSession();
      // start_session API returned, ab DB mein is_active=1 ho gaya hoga
      // Foran check karo status ko update karne ke liye
      await checkStatus();
    } catch (err) {
      alert("Session start nahi hua: " + err.message);
    }
    setLoading(false);
  };

  const stopSession = async () => {
    setLoading(true);
    try {
      await api.stopSession();
      setStatus("offline");
      setActiveAccount(null);
    } catch (err) {
      alert("Session stop nahi hua: " + err.message);
    }
    setLoading(false);
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
      
      {/* Left — Status */}
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${
          status === "online" ? "bg-green-400 animate-pulse" : 
          status === "starting" ? "bg-yellow-400 animate-pulse" : "bg-red-400"
        }`}/>
        <span className="text-white text-sm font-medium">
          {status === "online" ? `Active: ${activeAccount?.username}` :
           status === "starting" ? `Starting: ${activeAccount?.username} (Wait ~2 mins)` :
           "Session Offline"}
        </span>
        {activeAccount && (
          <span className="text-gray-400 text-xs">
            {(30 - activeAccount.hours_remaining).toFixed(1)}hr used
          </span>
        )}
      </div>

      {/* Right — Buttons */}
      <div className="flex items-center gap-3 relative">
        {status === "online" && (
          <div className="absolute top-12 right-0 bg-green-500/10 border border-green-500/30 text-green-400 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap shadow-lg">
            Notebook run ho chuki hai aur link mil chuka hai ab aap video bana sakte hain! 🎉
          </div>
        )}

        {(status === "offline" || status === "starting") ? (
          <button
            onClick={startSession}
            disabled={loading || status === "starting"}
            className={`${status === "starting" ? "bg-yellow-600" : "bg-green-500 hover:bg-green-600"} disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition`}
          >
            {loading || status === "starting" ? "Starting on Kaggle..." : "▶ Start Session"}
          </button>
        ) : (
          <button
            onClick={stopSession}
            disabled={loading}
            className="bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition"
          >
            {loading ? "Stopping..." : "⏹ Stop Session"}
          </button>
        )}
      </div>

    </div>
  );
}