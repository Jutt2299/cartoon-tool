import { useState, useEffect } from "react";
import api from "../api";

export default function Status() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getStatus();
        setStatus(data);
      } catch (err) {
        console.error(err);
      }
    }
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-4xl mx-auto pb-12 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">System Status</h1>
        <p className="text-gray-400">Live monitoring of your Kaggle sessions and API limits.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-dark rounded-2xl p-6 border border-gray-800">
          <h2 className="text-lg font-bold text-white mb-4">Kaggle Accounts</h2>
          {!status ? <div className="animate-pulse h-20 bg-gray-800 rounded-xl"></div> : 
            status.kaggle_accounts.map(acc => (
              <div key={acc.username} className="mb-4 last:mb-0">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">{acc.username}</span>
                  <span className="text-gray-400">{acc.hours_used.toFixed(1)} / 30 hrs</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{width: `${(acc.hours_used / 30) * 100}%`}}
                  ></div>
                </div>
              </div>
          ))}
        </div>

        <div className="glass-dark rounded-2xl p-6 border border-gray-800">
          <h2 className="text-lg font-bold text-white mb-4">ElevenLabs Usage</h2>
          {!status ? <div className="animate-pulse h-20 bg-gray-800 rounded-xl"></div> : 
            status.elevenlabs_keys.map(key => (
              <div key={key.id} className="mb-4 last:mb-0">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">...{key.api_key.slice(-4)}</span>
                  <span className="text-gray-400">{key.chars_used.toLocaleString()} / 10k chars</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div 
                    className="bg-purple-500 h-2 rounded-full" 
                    style={{width: `${(key.chars_used / 10000) * 100}%`}}
                  ></div>
                </div>
              </div>
          ))}
        </div>
      </div>
    </div>
  );
}
