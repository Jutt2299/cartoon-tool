import { useState, useEffect } from "react";
import { Download, Film, Trash2, AlertTriangle } from "lucide-react";
import api from "../api";
import { motion, AnimatePresence } from "framer-motion";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [deletingAll, setDeletingAll] = useState(false);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "https://alonejutt2288--cartoon-backend-fastapi-modal-app.modal.run";

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      setLoading(true);
      const data = await api.getHistory();
      setHistory(data.history || []);
    } catch (err) {
      console.error("Error loading history:", err);
    } finally {
      setLoading(false);
    }
  }

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

  const handleDeleteEpisode = async (episodeId) => {
    setDeletingId(episodeId);
    try {
      await api.deleteHistoryEpisode(episodeId);
      setHistory(prev => prev.filter(ep => ep.id !== episodeId));
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Delete failed! Try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleDeleteAll = async () => {
    setDeletingAll(true);
    try {
      await api.deleteAllHistory();
      setHistory([]);
      setConfirmDeleteAll(false);
    } catch (err) {
      console.error("Delete all failed:", err);
      alert("Delete all failed! Try again.");
    } finally {
      setDeletingAll(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto pb-12 animate-fade-in">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Episode History</h1>
          <p className="text-gray-400">View, download or delete your previously generated cartoons and shorts.</p>
        </div>
        {history.length > 0 && (
          <button
            onClick={() => setConfirmDeleteAll(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 border border-red-500/20 hover:border-red-500/40 transition-all text-sm font-medium"
          >
            <Trash2 size={15} />
            Delete All
          </button>
        )}
      </div>

      {/* Confirm Delete All Modal */}
      <AnimatePresence>
        {confirmDeleteAll && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 border border-red-500/30 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 rounded-xl bg-red-500/15">
                  <AlertTriangle size={22} className="text-red-400" />
                </div>
                <h3 className="text-lg font-bold text-white">Saari History Delete Karein?</h3>
              </div>
              <p className="text-gray-400 text-sm mb-6">
                Yeh action permanent hai. Tamam videos, thumbnails aur shorts hamesha ke liye delete ho jayenge. Kya aap sure hain?
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmDeleteAll(false)}
                  className="flex-1 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAll}
                  disabled={deletingAll}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-medium transition disabled:opacity-50"
                >
                  {deletingAll ? "Deleting..." : "Haan, Delete Karo"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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
          <AnimatePresence>
            {history.map((episode, idx) => (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: idx * 0.08 }}
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
                  {/* Delete button overlay */}
                  <button
                    onClick={() => handleDeleteEpisode(episode.id)}
                    disabled={deletingId === episode.id}
                    className="absolute top-3 left-3 opacity-0 group-hover:opacity-100 transition-all bg-red-600/80 hover:bg-red-600 backdrop-blur p-1.5 rounded-lg text-white disabled:opacity-50"
                    title="Delete this episode"
                  >
                    {deletingId === episode.id ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Trash2 size={14} />
                    )}
                  </button>
                </div>

                {/* Content */}
                <div className="p-5">
                  <h3 className="font-bold text-lg text-white mb-1 truncate" title={episode.title}>
                    {episode.title}
                  </h3>

                  <div className="mt-4 flex flex-col gap-2.5">
                    <button
                      onClick={() => handleDownload(episode.video_url, `${episode.title}.mp4`)}
                      className="flex items-center justify-center gap-2 w-full bg-primary-600 hover:bg-primary-500 text-white py-2.5 rounded-lg text-sm font-semibold transition"
                    >
                      <Download size={16} />
                      Download Episode
                    </button>

                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={() => handleDownload(episode.thumbnail_url, `${episode.title}_thumbnail.jpg`)}
                        className="flex items-center justify-center gap-1.5 glass bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-xs font-medium transition"
                      >
                        <Download size={12} /> Thumb
                      </button>
                      {episode.shorts_urls && episode.shorts_urls.length > 0 && (
                        <button
                          onClick={() => handleDownload(episode.shorts_urls[0], `${episode.title}_short.mp4`)}
                          className="flex items-center justify-center gap-1.5 glass bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-xs font-medium transition"
                        >
                          <Download size={12} /> Shorts
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteEpisode(episode.id)}
                        disabled={deletingId === episode.id}
                        className="flex items-center justify-center gap-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 py-2 rounded-lg text-xs font-medium transition disabled:opacity-50 border border-red-500/20"
                      >
                        <Trash2 size={12} />
                        {deletingId === episode.id ? "..." : "Delete"}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
