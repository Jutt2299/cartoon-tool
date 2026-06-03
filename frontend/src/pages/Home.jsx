import { useState } from "react";
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
    setGenerating(true);
    setProgress({
      stage: "Script parse ho rahi hai...",
      percent: 5
    });

    try {
      // Stage 1
      setProgress({ stage: "Script scenes mein toot rahi hai...", percent: 10 });
      await new Promise(r => setTimeout(r, 1000));

      // Stage 2
      setProgress({ stage: "Characters detect ho rahe hain...", percent: 20 });
      await new Promise(r => setTimeout(r, 1000));

      // Stage 3
      setProgress({ stage: "Kaggle session check ho raha hai...", percent: 30 });

      const result = await api.generateEpisode(script, episodeName);

      if (result.status === "success") {
        // Stage 4
        setProgress({ stage: "Videos ban rahi hain...", percent: 50 });
        await new Promise(r => setTimeout(r, 2000));

        // Stage 5
        setProgress({ stage: "Audio generate ho raha hai...", percent: 70 });
        await new Promise(r => setTimeout(r, 2000));

        // Stage 6
        setProgress({ stage: "Video assembly ho rahi hai...", percent: 90 });
        await new Promise(r => setTimeout(r, 2000));

        // Done
        setProgress({ stage: "Episode ban gaya! 🎉", percent: 100 });
        setDone(true);

      } else {
        setError(result.detail || "Kuch masla hua!");
      }

    } catch (err) {
      setError("Error: " + err.message);
    }

    setGenerating(false);
  };

  const handleReset = () => {
    setScript("");
    setEpisodeName("");
    setProgress(null);
    setDone(false);
    setError("");
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white pt-20 px-6 pb-10">
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            🎬 Cartoon Episode Generator
          </h1>
          <p className="text-gray-400 text-sm">
            Script paste karo — baaki sab automatic hoga!
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5 px-4 py-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Done State */}
        {done ? (
          <div className="bg-gray-900 border border-green-500/30 rounded-2xl p-8 text-center">
            <div className="text-5xl mb-4">🎉</div>
            <h2 className="text-xl font-bold text-green-400 mb-2">
              Episode Ban Gaya!
            </h2>
            <p className="text-gray-400 text-sm mb-6">
              "{episodeName}" successfully generate ho gaya!
            </p>
            <div className="flex gap-3 justify-center">
              <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition">
                ⬇️ Download Video
              </button>
              <button
                onClick={handleReset}
                className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition"
              >
                Naya Episode
              </button>
            </div>
          </div>

        ) : generating ? (
          /* Generating State */
          <ProgressBar
            stage={progress?.stage}
            percent={progress?.percent}
          />

        ) : (
          /* Input State */
          <div className="space-y-5">

            {/* Episode Name */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Episode Ka Naam
              </label>
              <input
                type="text"
                placeholder="Jaise: Episode 1 - Pehli Mulaqat"
                value={episodeName}
                onChange={e => setEpisodeName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 text-white placeholder-gray-500"
              />
            </div>

            {/* Script Input Component */}
            <ScriptInput value={script} onChange={setScript} />

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3.5 rounded-xl font-semibold text-base transition"
            >
              🎬 Episode Generate Karo
            </button>

            {/* Info box */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-400 leading-relaxed">
                💡 <strong className="text-gray-300">Yaad rakho:</strong> Generate
                karne se pehle upar{" "}
                <strong className="text-green-400">Start Session</strong> dabao —
                warna video nahi banegi!
              </p>
            </div>

            {/* Script Format Guide */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-sm font-medium text-gray-300 mb-3">
                📝 Script Format Guide:
              </p>
              <pre className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap">
{`SCENE 1: Ahmed ka ghar - drawing room

[Ahmed sofa pe baitha TV dekh raha hai]

Ahmed: "Yaar kitni boring movie hai!"
Mama: "Ahmed! Khana khane aa jao!"
Ahmed: "Abhi aa raha hoon Mama!"

SCENE 2: Kitchen

[Mama khana bana rahi hai]

Mama: "Yeh larki bhi na!"`}
              </pre>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}