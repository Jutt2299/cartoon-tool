const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = {

  // Session
  startSession: async () => {
    const res = await fetch(`${BASE_URL}/session/start`, { method: "POST" });
    return res.json();
  },

  stopSession: async () => {
    const res = await fetch(`${BASE_URL}/session/stop`, { method: "POST" });
    return res.json();
  },

  getStatus: async () => {
    const res = await fetch(`${BASE_URL}/settings/status`);
    return res.json();
  },

  // Generate
  generateEpisode: async (scriptText, episodeName) => {
    const res = await fetch(`${BASE_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        script_text: scriptText,
        episode_name: episodeName
      })
    });
    return res.json();
  },

  // Kaggle Settings
  addKaggleAccount: async (username, token) => {
    const res = await fetch(`${BASE_URL}/settings/kaggle/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, token })
    });
    return res.json();
  },

  deleteKaggleAccount: async (username) => {
    const res = await fetch(`${BASE_URL}/settings/kaggle/${username}`, {
      method: "DELETE"
    });
    return res.json();
  },

  // ElevenLabs Settings
  addElevenLabsKey: async (apiKey) => {
    const res = await fetch(`${BASE_URL}/settings/elevenlabs/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey })
    });
    return res.json();
  },

  deleteElevenLabsKey: async (keyId) => {
    const res = await fetch(`${BASE_URL}/settings/elevenlabs/${keyId}`, {
      method: "DELETE"
    });
    return res.json();
  },

};

export default api;