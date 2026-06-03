export default function ProgressBar({ stage, percent }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">

      {/* Icon + Stage */}
      <div className="mb-6 text-center">
        <div className="text-4xl mb-3 animate-bounce">⚙️</div>
        <p className="text-white font-medium">{stage}</p>
      </div>

      {/* Bar */}
      <div className="w-full bg-gray-800 rounded-full h-3 mb-2">
        <div
          className="bg-blue-500 h-3 rounded-full transition-all duration-500"
          style={{ width: `${percent || 0}%` }}
        />
      </div>

      {/* Percent */}
      <p className="text-right text-xs text-gray-400 mb-4">
        {percent || 0}%
      </p>

      {/* Stages list */}
      <div className="space-y-2 mt-4">
        {[
          { label: "Script parse", threshold: 10 },
          { label: "Characters detect", threshold: 20 },
          { label: "Kaggle session", threshold: 30 },
          { label: "Video generation", threshold: 60 },
          { label: "Audio generation", threshold: 75 },
          { label: "Video assembly", threshold: 90 },
          { label: "Complete!", threshold: 100 },
        ].map((s, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              percent >= s.threshold
                ? "bg-green-400"
                : "bg-gray-600"
            }`} />
            <p className={`text-xs ${
              percent >= s.threshold
                ? "text-green-400"
                : "text-gray-500"
            }`}>
              {s.label}
            </p>
          </div>
        ))}
      </div>

      <p className="text-center text-gray-500 text-xs mt-6">
        Chai pi lo — thodi der lagegi ☕
      </p>
    </div>
  );
}