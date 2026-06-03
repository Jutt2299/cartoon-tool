import { useState } from "react";
import Home from "./pages/Home";
import Settings from "./pages/Settings";
import SessionBar from "./components/SessionBar";

export default function App() {
  const [page, setPage] = useState("home");

  return (
    <div className="bg-gray-950 min-h-screen">

      {/* Top Session Bar */}
      <SessionBar />

      {/* Navigation */}
      <div className="fixed top-12 left-0 right-0 z-40 bg-gray-900 border-b border-gray-800 px-6 py-2 flex gap-4">
        <button
          onClick={() => setPage("home")}
          className={`text-sm px-3 py-1.5 rounded-lg transition ${
            page === "home"
              ? "bg-blue-600 text-white"
              : "text-gray-400 hover:text-white"
          }`}
        >
          🎬 Generate
        </button>
        <button
          onClick={() => setPage("settings")}
          className={`text-sm px-3 py-1.5 rounded-lg transition ${
            page === "settings"
              ? "bg-blue-600 text-white"
              : "text-gray-400 hover:text-white"
          }`}
        >
          ⚙️ Settings
        </button>
      </div>

      {/* Pages */}
      <div className="pt-10">
        {page === "home" && <Home />}
        {page === "settings" && <Settings />}
      </div>

    </div>
  );
}