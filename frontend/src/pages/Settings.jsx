import { useState, useEffect } from "react";
import api from "../api";

export default function Settings() {
  const [statusData, setStatusData] = useState(null);
  
  // Forms state
  const [kaggleUser, setKaggleUser] = useState("");
  const [kaggleToken, setKaggleToken] = useState("");
  const [elevenKey, setElevenKey] = useState("");
  
  const [globalNgrok, setGlobalNgrok] = useState("");
  const [globalHf, setGlobalHf] = useState("");
  const [globalGemini, setGlobalGemini] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ text: "", type: "" });

  const loadStatus = async () => {
    try {
      const data = await api.getStatus();
      setStatusData(data);
      if (data.global_settings) {
        setGlobalNgrok(data.global_settings.ngrok_token || "");
        setGlobalHf(data.global_settings.hf_token || "");
        setGlobalGemini(data.global_settings.gemini_api_key || "");
      }
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

  const handleSaveGlobal = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.saveGlobalSettings(globalNgrok, globalHf, globalGemini);
      showMsg("Global Tokens saved successfully!");
      loadStatus();
    } catch (err) {
      showMsg("Error saving global tokens", "error");
    }
    setLoading(false);
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

      {/* Global Tokens Section */}
      <div className="mb-8 glass-dark rounded-2xl p-6 border border-gray-800">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-yellow-400">🌍</span> Global Tokens
        </h2>
        <p className="text-sm text-gray-400 mb-6">Yeh tokens sab Kaggle notebooks ke liye use honge (Ngrok tunnel aur HuggingFace model download ke liye).</p>
        
        <form onSubmit={handleSaveGlobal} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Ngrok Token</label>
              <input 
                type="password" placeholder="Ngrok Auth Token" required
                value={globalNgrok} onChange={e => setGlobalNgrok(e.target.value)}
                className="w-full glass bg-[#0B0C10]/80 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-yellow-500 text-white placeholder-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">HuggingFace Token</label>
              <input 
                type="password" placeholder="HF Token (Read Access)" required
                value={globalHf} onChange={e => setGlobalHf(e.target.value)}
                className="w-full glass bg-[#0B0C10]/80 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-yellow-500 text-white placeholder-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Gemini API Key</label>
              <input 
                type="password" placeholder="Google Gemini AI Key" required
                value={globalGemini} onChange={e => setGlobalGemini(e.target.value)}
                className="w-full glass bg-[#0B0C10]/80 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-yellow-500 text-white placeholder-gray-600"
              />
            </div>
          </div>
          <button disabled={loading} type="submit" className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-2.5 rounded-lg text-sm font-medium transition disabled:opacity-50 mt-2">
            Save Global Tokens
          </button>
        </form>
      </div>

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
                statusData.kaggle_accounts.map(acc => {
                  const hoursLeft = acc.hours_remaining ?? (30 - (acc.hours_used || 0));
                  const pct = Math.max(0, Math.min(100, (hoursLeft / 30) * 100));
                  const barColor = hoursLeft > 15 ? 'bg-green-500' : hoursLeft > 5 ? 'bg-yellow-500' : 'bg-red-500';
                  return (
                    <div key={acc.username} className="glass bg-white/5 p-4 rounded-lg border border-white/5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="font-medium text-gray-200">{acc.username}</div>
                          {acc.is_active ? (
                            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full border border-green-500/30">● Active</span>
                          ) : (
                            <span className="text-xs bg-gray-700/50 text-gray-500 px-2 py-0.5 rounded-full">Idle</span>
                          )}
                        </div>
                        <button onClick={() => handleDeleteKaggle(acc.username)} className="text-red-400 hover:text-red-300 text-sm font-medium px-2 py-1 rounded hover:bg-red-500/10 transition">
                          Remove
                        </button>
                      </div>
                      {/* GPU Hours Bar */}
                      <div className="mt-1">
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                          <span>GPU Quota (Weekly)</span>
                          <span className={hoursLeft > 5 ? 'text-green-400' : 'text-red-400'}>
                            {hoursLeft.toFixed(1)} / 30 hrs left
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className={`${barColor} h-2 rounded-full transition-all duration-500`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })
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