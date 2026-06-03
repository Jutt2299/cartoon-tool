import { useState, useEffect } from "react";
import { Download, Film, MoreVertical } from "lucide-react";
import api from "../api";
import { motion } from "framer-motion";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Use the actual API URL to resolve relative media paths from the backend
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    async function loadHistory() {
      try {
        const data = await api.getHistory();
        setHistory(data.history || []);
      } catch (err) {
        console.error("Error loading history:", err);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  const handleDownload = async (url, filename) => {
    try {
      const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
      const response = await fetch(fullUrl);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      a.remove();
    } catch (e) {
      window.open(url.startsWith('http') ? url : `${API_URL}${url}`, '_blank');
    }
  };

  return (
    <div className="max-w-6xl mx-auto pb-12 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Episode History</h1>
        <p className="text-gray-400">View and download your previously generated cartoons and shorts.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-dark rounded-2xl overflow-hidden animate-pulse">
              <div className="w-full aspect-video bg-gray-800"></div>
              <div className="p-5">
                <div className="h-6 bg-gray-800 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-800 rounded w-1/2 mb-6"></div>
                <div className="flex gap-2">
                  <div className="h-10 bg-gray-800 rounded flex-1"></div>
                  <div className="h-10 bg-gray-800 rounded w-24"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-20 glass-dark rounded-3xl border border-gray-800">
          <Film size={48} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-bold text-gray-300">No episodes yet</h2>
          <p className="text-gray-500 mt-2">Generate your first cartoon to see it here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {history.map((episode, idx) => (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              key={episode.id} 
              className="glass-dark rounded-2xl overflow-hidden border border-gray-800 hover:border-primary-500/30 transition-all group"
            >
              {/* Thumbnail */}
              <div className="relative aspect-video bg-gray-900 overflow-hidden">
                {episode.thumbnail_url ? (
                  <img 
                    src={episode.thumbnail_url.startsWith('http') ? episode.thumbnail_url : `${API_URL}${episode.thumbnail_url}`} 
                    alt={episode.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Film className="text-gray-700" size={32} />
                  </div>
                )}
                <div className="absolute top-3 right-3 bg-black/60 backdrop-blur px-2.5 py-1 rounded text-xs font-medium text-white">
                  {new Date(episode.created_at).toLocaleDateString()}
                </div>
              </div>

              {/* Content */}
              <div className="p-5">
                <h3 className="font-bold text-lg text-white mb-1 truncate" title={episode.title}>
                  {episode.title}
                </h3>
                
                <div className="mt-5 flex flex-col gap-3">
                  <button 
                    onClick={() => handleDownload(episode.video_url, `${episode.title}.mp4`)}
                    className="flex items-center justify-center gap-2 w-full bg-primary-600 hover:bg-primary-500 text-white py-2.5 rounded-lg text-sm font-semibold transition"
                  >
                    <Download size={16} />
                    Download Episode
                  </button>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <button 
                       onClick={() => handleDownload(episode.thumbnail_url, `${episode.title}_thumbnail.jpg`)}
                       className="flex items-center justify-center gap-2 glass bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-xs font-medium transition"
                    >
                      <Download size={14} /> Thumbnail
                    </button>
                    {episode.shorts_urls && episode.shorts_urls.length > 0 && (
                      <button 
                         onClick={() => handleDownload(episode.shorts_urls[0], `${episode.title}_short.mp4`)}
                         className="flex items-center justify-center gap-2 glass bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-xs font-medium transition"
                      >
                        <Download size={14} /> Get Shorts
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
