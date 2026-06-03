import { useState, useEffect } from "react";
import api from "../api";

export default function Settings() {
  const [kaggleAccounts, setKaggleAccounts] = useState([]);
  const [elevenLabsKeys, setElevenLabsKeys] = useState([]);
  const [newKaggle, setNewKaggle] = useState({ username: "", token: "" });
  const [newElevenKey, setNewElevenKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await api.getStatus();
      setKaggleAccounts(data.kaggle_accounts);
      setElevenLabsKeys(data.elevenlabs_keys);
    } catch (err) {
      showMessage("Status load nahi hua!", "error");
    }
  };

  const showMessage = (msg, type = "success") => {
    setMessage({ text: msg, type });
    setTimeout(() => setMessage(""), 3000);
  };

  // ── Kaggle ──────────────────────────

  const addKaggleAccount = async () => {
    if (!newKaggle.username || !newKaggle.token) {
      showMessage("Username aur Token dono chahiye!", "error");
      return;
    }
    setLoading(true);
    try {
      await api.addKaggleAccount(newKaggle.username, newKaggle.token);
      setNewKaggle({ username: "", token: "" });
      await loadStatus();
      showMessage("Kaggle account add ho gaya! ✅");
    } catch (err) {
      showMessage("Account add nahi hua!", "error");
    }
    setLoading(false);
  };

  const deleteKaggleAccount = async (username) => {
    if (!confirm(`${username} delete karna chahte ho?`)) return;
    try {
      await api.deleteKaggleAccount(username);
      await loadStatus();
      showMessage("Account delete ho gaya!");
    } catch (err) {
      showMessage("Delete nahi hua!", "error");
    }
  };

  // ── ElevenLabs ──────────────────────

  const addElevenLabsKey = async () => {
    if (!newElevenKey) {
      showMessage("API Key daalo!", "error");
      return;
    }
    setLoading(true);
    try {
      await api.addElevenLabsKey(newElevenKey);
      setNewElevenKey("");
      await loadStatus();
      showMessage("ElevenLabs key add ho gayi! ✅");
    } catch (err) {
      showMessage("Key add nahi hui!", "error");
    }
    setLoading(false);
  };

  const deleteElevenLabsKey = async (keyId) => {
    if (!confirm("Yeh key delete karna chahte ho?")) return;
    try {
      await api.deleteElevenLabsKey(keyId);
      await loadStatus();
      showMessage("Key delete ho gayi!");
    } catch (err) {
      showMessage("Delete nahi hua!", "error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white pt-20 px-6 pb-10">
      <div className="max-w-3xl mx-auto">

        <h1 className="text-2xl font-bold mb-8">⚙️ Settings</h1>

        {/* Message */}
        {message && (
          <div className={`mb-6 px-4 py-3 rounded-lg text-sm font-medium ${
            message.type === "error"
              ? "bg-red-500/20 text-red-400 border border-red-500/30"
              : "bg-green-500/20 text-green-400 border border-green-500/30"
          }`}>
            {message.text}
          </div>
        )}

        {/* ── Kaggle Accounts ── */}
        <div className="bg-gray-900 rounded-2xl p-6 mb-6 border border-gray-800">
          <h2 className="text-lg font-semibold mb-5">
            🖥️ Kaggle Accounts
          </h2>

          {/* Existing accounts */}
          <div className="space-y-3 mb-5">
            {kaggleAccounts.length === 0 && (
              <p className="text-gray-500 text-sm">
                Koi account nahi — neeche add karo
              </p>
            )}
            {kaggleAccounts.map((acc, i) => (
              <div
                key={i}
                className="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${
                    acc.is_active ? "bg-green-400 animate-pulse" : "bg-gray-500"
                  }`}/>
                  <div>
                    <p className="text-sm font-medium">{acc.username}</p>
                    <p className="text-xs text-gray-400">
                      {acc.hours_remaining?.toFixed(1) || 30}hr remaining
                    </p>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="flex items-center gap-4">
                  <div className="w-24 bg-gray-700 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{
                        width: `${((acc.hours_used || 0) / 30) * 100}%`
                      }}
                    />
                  </div>
                  <button
                    onClick={() => deleteKaggleAccount(acc.username)}
                    className="text-red-400 hover:text-red-300 text-xs"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Add new account */}
          <div className="border-t border-gray-800 pt-5">
            <p className="text-sm text-gray-400 mb-3">Naya account add karo:</p>
            <div className="flex gap-3 mb-3">
              <input
                type="text"
                placeholder="Kaggle Username"
                value={newKaggle.username}
                onChange={e => setNewKaggle({ ...newKaggle, username: e.target.value })}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex gap-3">
              <input
                type="password"
                placeholder="Kaggle API Token"
                value={newKaggle.token}
                onChange={e => setNewKaggle({ ...newKaggle, token: e.target.value })}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={addKaggleAccount}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
              >
                + Add
              </button>
            </div>
          </div>
        </div>

        {/* ── ElevenLabs Keys ── */}
        <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
          <h2 className="text-lg font-semibold mb-5">
            🎙️ ElevenLabs API Keys
          </h2>

          {/* Existing keys */}
          <div className="space-y-3 mb-5">
            {elevenLabsKeys.length === 0 && (
              <p className="text-gray-500 text-sm">
                Koi key nahi — neeche add karo
              </p>
            )}
            {elevenLabsKeys.map((key, i) => (
              <div
                key={i}
                className="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${
                    key.is_active ? "bg-green-400 animate-pulse" : "bg-gray-500"
                  }`}/>
                  <div>
                    <p className="text-sm font-medium">Key #{key.id}</p>
                    <p className="text-xs text-gray-400">
                      {key.chars_remaining} chars remaining
                    </p>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="flex items-center gap-4">
                  <div className="w-24 bg-gray-700 rounded-full h-1.5">
                    <div
                      className="bg-purple-500 h-1.5 rounded-full"
                      style={{
                        width: `${(key.chars_used / 10000) * 100}%`
                      }}
                    />
                  </div>
                  <button
                    onClick={() => deleteElevenLabsKey(key.id)}
                    className="text-red-400 hover:text-red-300 text-xs"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Add new key */}
          <div className="border-t border-gray-800 pt-5">
            <p className="text-sm text-gray-400 mb-3">Naya key add karo:</p>
            <div className="flex gap-3">
              <input
                type="password"
                placeholder="ElevenLabs API Key"
                value={newElevenKey}
                onChange={e => setNewElevenKey(e.target.value)}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={addElevenLabsKey}
                disabled={loading}
                className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
              >
                + Add
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}