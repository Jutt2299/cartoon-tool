const BASE_URL = "https://alonejutt2288--cartoon-backend-fastapi-modal-app.modal.run";

const api = {

  // Session
  startSession: async () => {
    const res = await fetch(`${BASE_URL}/session/start`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Unknown error");
    return data;
  },

  stopSession: async () => {
    const res = await fetch(`${BASE_URL}/session/stop`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Unknown error");
    return data;
  },

  getGlobalSettings: async () => {
    const res = await fetch(`${BASE_URL}/settings/global`);
    return res.json();
  },

  saveGlobalSettings: async (ngrokToken, hfToken, geminiApiKey) => {
    const res = await fetch(`${BASE_URL}/settings/global`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        ngrok_token: ngrokToken, 
        hf_token: hfToken,
        gemini_api_key: geminiApiKey 
      })
    });
    return res.json();
  },

  getStatus: async () => {
    const res = await fetch(`${BASE_URL}/settings/status?t=${Date.now()}`);
    return res.json();
  },

  getHistory: async () => {
    const res = await fetch(`${BASE_URL}/history`);
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

  getJobStatus: async (jobId) => {
    const res = await fetch(`${BASE_URL}/job/${jobId}/status`);
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