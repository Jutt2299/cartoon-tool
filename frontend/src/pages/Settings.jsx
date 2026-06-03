import { useState, useEffect } from "react";
import api from "../api";

export default function Settings() {
  const [statusData, setStatusData] = useState(null);
  
  // Forms state
  const [kaggleUser, setKaggleUser] = useState("");
  const [kaggleToken, setKaggleToken] = useState("");
  const [elevenKey, setElevenKey] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ text: "", type: "" });

  const loadStatus = async () => {
    try {
      const data = await api.getStatus();
      setStatusData(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const showMsg = (text, type="success") => {
    setMsg({ text, type });
    setTimeout(() => setMsg({ text: "", type: "" }), 3000);
  };

    const handleAddKaggle = async (e) => {
    e.preventDefault();
    setLoading(true);
    showMsg("Setting up Kaggle Notebook (Takes ~30s)...", "success");
    try {
      const res = await api.addKaggleAccount(kaggleUser, kaggleToken);
      showMsg(res.message || "Kaggle account & Notebook added!");
      setKaggleUser("");
      setKaggleToken("");
      loadStatus();
    } catch (err) {
      showMsg("Error setting up account", "error");
    }
    setLoading(false);
  };

  const handleDeleteKaggle = async (username) => {
    try {
      await api.deleteKaggleAccount(username);
      showMsg("Account deleted");
      loadStatus();
    } catch (err) {
      showMsg("Error deleting", "error");
    }
  };

  const handleAddEleven = async (e) => {
    e.preventDefault();
    setLoading(true);
    showMsg("Verifying API Key...", "success");
    try {
      const res = await api.addElevenLabsKey(elevenKey);
      showMsg(`Key verified! ${res.chars_remaining} chars remaining.`);
      setElevenKey("");
      loadStatus();
    } catch (err) {
      showMsg("Error adding or verifying key", "error");
    }
    setLoading(false);
  };

  const handleDeleteEleven = async (id) => {
    try {
      await api.deleteElevenLabsKey(id);
      showMsg("Key deleted");
      loadStatus();
    } catch (err) {
      showMsg("Error deleting", "error");
    }
  };

  return (
    <div className="max-w-4xl mx-auto pb-12 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">API Settings</h1>
        <p className="text-gray-400">Manage your Kaggle and ElevenLabs credentials for AI generation.</p>
      </div>

      {msg.text && (
        <div className={`mb-6 p-4 rounded-xl border ${msg.type === "error" ? "bg-red-500/10 border-red-500/30 text-red-400" : "bg-green-500/10 border-green-500/30 text-green-400"}`}>
          {msg.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Kaggle Section */}
        <div className="space-y-6">
          <div className="glass-dark rounded-2xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-blue-400">📊</span> Kaggle Accounts
            </h2>
            
            <form onSubmit={handleAddKaggle} className="space-y-4 mb-6">
              <div>
                <input 
                  type="text" placeholder="Username" required
                  value={kaggleUser} onChange={e => setKaggleUser(e.target.value)}
                  className="w-full glass bg-[#0B0C10]/80 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 text-white placeholder-gray-600"
                />
              </div>
              <div>
                <input 
                  type="password" placeholder="API Token" required
                  value={kaggleToken} onChange={e => setKaggleToken(e.target.value)}
                  className="w-full glass bg-[#0B0C10]/80 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 text-white placeholder-gray-600"
                />
              </div>
              <button disabled={loading} type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg text-sm font-medium transition disabled:opacity-50">
                Add & Auto-Setup Notebook
              </button>
            </form>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Saved Accounts</h3>
              {!statusData ? <p className="text-sm text-gray-500">Loading...</p> : 
                statusData.kaggle_accounts.length === 0 ? <p className="text-sm text-gray-500">No accounts saved</p> :
                statusData.kaggle_accounts.map(acc => (
                  <div key={acc.username} className="flex items-center justify-between glass bg-white/5 p-3 rounded-lg border border-white/5">
                    <div>
                      <div className="font-medium text-gray-200">{acc.username}</div>
                      <div className="text-xs text-green-400">✓ Notebook Ready</div>
                    </div>
                    <button onClick={() => handleDeleteKaggle(acc.username)} className="text-red-400 hover:text-red-300 text-sm font-medium px-2 py-1 rounded hover:bg-red-500/10 transition">
                      Remove
                    </button>
                  </div>
                ))
              }
            </div>
          </div>
        </div>

        {/* ElevenLabs Section */}
        <div className="space-y-6">
          <div className="glass-dark rounded-2xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-purple-400">🎙️</span> ElevenLabs Keys
            </h2>
            
            <form onSubmit={handleAddEleven} className="space-y-4 mb-6">
              <div>
                <input 
                  type="password" placeholder="API Key" required
                  value={elevenKey} onChange={e => setElevenKey(e.target.value)}
                  className="w-full glass bg-[#0B0C10]/80 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-purple-500 text-white placeholder-gray-600"
                />
              </div>
              <button disabled={loading} type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2.5 rounded-lg text-sm font-medium transition disabled:opacity-50">
                Verify & Add API Key
              </button>
            </form>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Saved Keys</h3>
              {!statusData ? <p className="text-sm text-gray-500">Loading...</p> : 
                statusData.elevenlabs_keys.length === 0 ? <p className="text-sm text-gray-500">No keys saved</p> :
                statusData.elevenlabs_keys.map(key => (
                  <div key={key.id} className="flex items-center justify-between glass bg-white/5 p-3 rounded-lg border border-white/5">
                    <div>
                      <div className="font-medium text-gray-200">...{key.api_key.slice(-4)}</div>
                      <div className="text-xs text-purple-400">{key.chars_remaining || (10000 - key.chars_used)} chars left</div>
                    </div>
                    <button onClick={() => handleDeleteEleven(key.id)} className="text-red-400 hover:text-red-300 text-sm font-medium px-2 py-1 rounded hover:bg-red-500/10 transition">
                      Remove
                    </button>
                  </div>
                ))
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}