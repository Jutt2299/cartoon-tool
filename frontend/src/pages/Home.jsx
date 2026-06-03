import { useState, useRef, useEffect } from "react";
import api from "../api";
import ScriptInput from "../components/ScriptInput";
import ProgressBar from "../components/ProgressBar";

export default function Home() {
  const [episodeName, setEpisodeName] = useState("");
  const [script, setScript] = useState("");
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  
  const videoRef = useRef(null);

  // Fallback demo video link for testing if backend doesn't provide one
  const DEMO_VIDEO_URL = "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4";

  const handleGenerate = async () => {
    if (!episodeName.trim()) {
      setError("Episode ka naam daalo!");
      return;
    }
    if (!script.trim()) {
      setError("Script daalo!");
      return;
    }

    setError("");
    setDone(false);
    setVideoUrl(null);
    setGenerating(true);
    setProgress({
      stage: "Script submit ho rahi hai...",
      percent: 5
    });

    try {
      // Step 1: Start background job
      const result = await api.generateEpisode(script, episodeName);

      if (result.status === "queued") {
        const jobId = result.job_id;
        
        // Step 2: Poll for status
        const pollInterval = setInterval(async () => {
          try {
            const statusResult = await api.getJobStatus(jobId);
            
            setProgress({ 
              stage: statusResult.progress_msg || "Processing...", 
              percent: statusResult.progress || 10 
            });

            if (statusResult.status === "done") {
              clearInterval(pollInterval);
              
              let generatedVideoUrl = DEMO_VIDEO_URL;
              if (statusResult.video_url) {
                // We use base API URL + relative video_url
                const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
                generatedVideoUrl = `${BASE_URL}${statusResult.video_url}`;
              }

              setVideoUrl(generatedVideoUrl);
              setProgress({ stage: "Episode ban gaya! 🎉", percent: 100 });
              setDone(true);
              setGenerating(false);
            } else if (statusResult.status === "error") {
              clearInterval(pollInterval);
              setError(statusResult.error || "Kuch masla hua!");
              setGenerating(false);
            }
          } catch (pollErr) {
            console.error("Polling error:", pollErr);
            // Keep polling unless it's a persistent error
          }
        }, 3000); // Poll every 3 seconds

      } else {
        setError(result.detail || "Kuch masla hua!");
        setGenerating(false);
      }

    } catch (err) {
      setError("Error: " + err.message);
      setGenerating(false);
    }
  };

  const handleReset = () => {
    setScript("");
    setEpisodeName("");
    setProgress(null);
    setDone(false);
    setError("");
    setVideoUrl(null);
  };

  const handleDownload = async () => {
    if (!videoUrl) return;
    try {
      // Direct download logic
      const response = await fetch(videoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${episodeName || "cartoon_episode"}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (e) {
      // Fallback if CORS prevents blob download
      const a = document.createElement("a");
      a.href = videoUrl;
      a.download = `${episodeName || "cartoon_episode"}.mp4`;
      a.target = "_blank";
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  };

  return (
    <div className="min-h-screen pt-24 px-6 pb-12 relative overflow-hidden">
      
      {/* Background Animated Blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary-500/20 rounded-full mix-blend-screen filter blur-[100px] animate-blob"></div>
        <div className="absolute top-[20%] right-[-5%] w-96 h-96 bg-accent-500/20 rounded-full mix-blend-screen filter blur-[100px] animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-20%] left-[20%] w-[500px] h-[500px] bg-purple-500/20 rounded-full mix-blend-screen filter blur-[120px] animate-blob animation-delay-4000"></div>
      </div>

      <div className="max-w-4xl mx-auto relative z-10">
        
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-block mb-4 px-4 py-1.5 rounded-full border border-primary-500/30 bg-primary-500/10 text-primary-400 text-sm font-semibold tracking-wide backdrop-blur-md">
            ✨ AI Powered Animation
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-4 tracking-tight">
            Cartoon <span className="text-gradient">Episode</span> Generator
          </h1>
          <p className="text-gray-400 text-lg max-w-xl mx-auto mb-10">
            Script paste karo, aur hamari AI magic se pura episode banate dekho.
          </p>

          {/* How It Works */}
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 mb-12 max-w-2xl mx-auto text-sm font-medium">
            <div className="flex flex-col items-center gap-2 glass px-6 py-4 rounded-2xl border-gray-800/50 flex-1 w-full relative">
              <div className="w-10 h-10 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-lg mb-1">📝</div>
              <div className="text-gray-200">1. Write Script</div>
              {/* Arrow */}
              <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-gray-600">→</div>
            </div>
            
            <div className="flex flex-col items-center gap-2 glass px-6 py-4 rounded-2xl border-gray-800/50 flex-1 w-full relative">
              <div className="w-10 h-10 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center text-lg mb-1">⚡</div>
              <div className="text-gray-200">2. Generate</div>
              {/* Arrow */}
              <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-gray-600">→</div>
            </div>

            <div className="flex flex-col items-center gap-2 glass px-6 py-4 rounded-2xl border-gray-800/50 flex-1 w-full">
              <div className="w-10 h-10 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-lg mb-1">⬇️</div>
              <div className="text-gray-200">3. Download</div>
            </div>
          </div>
        </div>

        {/* Main Interface Container */}
        <div className="glass-dark rounded-3xl p-6 md:p-10 shadow-2xl animate-slide-up border border-gray-700/50 relative overflow-hidden">
          
          {/* Subtle top border glow */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-primary-500/50 to-transparent"></div>

          {/* Error Message */}
          {error && (
            <div className="mb-8 px-6 py-4 glass border-red-500/40 rounded-2xl flex items-center gap-4 animate-fade-in">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xl">⚠️</div>
              <div className="text-red-200 font-medium">{error}</div>
            </div>
          )}

          {done ? (
            /* Result State - Video Player */
            <div className="animate-fade-in flex flex-col items-center">
              
              <div className="w-full max-w-3xl mb-8 relative group">
                {/* Decorative glow behind video */}
                <div className="absolute -inset-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-2xl blur opacity-30 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                
                {/* Video Player */}
                <div className="relative rounded-2xl overflow-hidden bg-black aspect-video border border-white/10 shadow-2xl">
                  {videoUrl ? (
                     <video 
                       ref={videoRef}
                       src={videoUrl} 
                       controls 
                       autoPlay
                       className="w-full h-full object-cover"
                     />
                  ) : (
                     <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
                        <span className="text-4xl mb-3">🎥</span>
                        <p>Video Load Nahi Ho Saki</p>
                     </div>
                  )}
                </div>
              </div>

              <h2 className="text-3xl font-bold text-white mb-2">
                Episode <span className="text-green-400">Ready!</span> 🎉
              </h2>
              <p className="text-gray-400 mb-8 text-center max-w-md">
                Aapka episode "{episodeName}" successfully generate ho gaya hai. Aap ise dekh sakte hain ya download kar sakte hain.
              </p>

              <div className="flex flex-wrap gap-4 justify-center w-full">
                <button 
                  onClick={handleDownload}
                  className="relative flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all duration-300 hover:scale-105 hover:shadow-[0_0_20px_rgba(139,92,246,0.4)]"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                  Download Video
                </button>
                <button
                  onClick={handleReset}
                  className="flex items-center justify-center gap-2 glass hover:bg-white/10 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all duration-300 hover:scale-105"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path></svg>
                  Naya Episode Banayein
                </button>
              </div>
            </div>

          ) : generating ? (
            /* Generating State */
            <div className="py-12 animate-fade-in flex flex-col items-center">
              <div className="relative mb-8">
                 <div className="w-24 h-24 rounded-full border-4 border-gray-800 border-t-primary-500 animate-spin"></div>
                 <div className="absolute inset-0 w-24 h-24 rounded-full blur-xl bg-primary-500/30 animate-pulse-glow"></div>
              </div>
              <ProgressBar
                stage={progress?.stage}
                percent={progress?.percent}
              />
            </div>

          ) : (
            /* Input State */
            <div className="space-y-8 animate-fade-in">
              
              {/* Episode Name */}
              <div className="space-y-3">
                <label className="block text-sm font-semibold text-gray-300 ml-1">
                  Episode Ka Naam
                </label>
                <div className="relative group">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl blur opacity-20 group-focus-within:opacity-50 transition duration-500"></div>
                  <input
                    type="text"
                    placeholder="Jaise: Episode 1 - Pehli Mulaqat"
                    value={episodeName}
                    onChange={e => setEpisodeName(e.target.value)}
                    className="relative w-full glass bg-[#0B0C10]/80 rounded-xl px-5 py-4 text-base focus:outline-none focus:ring-2 focus:ring-primary-500/50 text-white placeholder-gray-600 transition-all"
                  />
                </div>
              </div>

              {/* Script Input Component */}
              <div className="space-y-3">
                <label className="block text-sm font-semibold text-gray-300 ml-1">
                  Script Details
                </label>
                <ScriptInput value={script} onChange={setScript} />
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                className="relative w-full group overflow-hidden rounded-xl font-bold text-lg p-[1px]"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-primary-500 via-accent-500 to-primary-500 opacity-70 group-hover:opacity-100 transition-opacity duration-300"></span>
                <div className="relative w-full h-full bg-[#0B0C10] group-hover:bg-transparent transition-colors duration-300 rounded-xl px-8 py-5 flex items-center justify-center gap-3">
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-accent-400 group-hover:text-white transition-colors duration-300">
                    🎬 Episode Generate Karo
                  </span>
                  <svg className="w-5 h-5 text-accent-400 group-hover:text-white transition-colors duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </div>
              </button>

              {/* Info Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="glass bg-white/5 rounded-2xl p-5 border border-white/5 hover:border-primary-500/30 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">💡</span>
                    <h3 className="font-semibold text-gray-200">Session Rule</h3>
                  </div>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    Generate karne se pehle top bar mein <strong className="text-primary-400">Start Session</strong> dabana zaroori hai, warna Kaggle/ElevenLabs block ho jayega.
                  </p>
                </div>
                
                <div className="glass bg-white/5 rounded-2xl p-5 border border-white/5 hover:border-accent-500/30 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">📝</span>
                    <h3 className="font-semibold text-gray-200">Script Format</h3>
                  </div>
                  <pre className="text-xs text-gray-400 leading-relaxed font-mono">
                    SCENE 1: Ahmed ka ghar{"\n\n"}
                    [Ahmed sofa pe hai]{"\n\n"}
                    Ahmed: "Hello Mama!"{"\n"}
                    Mama: "Khana khao!"
                  </pre>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}