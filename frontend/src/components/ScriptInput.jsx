export default function ScriptInput({ value, onChange }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Script
      </label>
      <p className="text-xs text-gray-500 mb-3">
        Format:{" "}
        <span className="text-gray-400">
          SCENE 1: Location | [Action] | Character: "Dialogue"
        </span>
      </p>
      <textarea
        placeholder={`SCENE 1: Ahmed ka ghar\n\n[Ahmed sofa pe baitha hai]\n\nAhmed: "Yaar kya ho raha hai!"\nMama: "Khana khao!"`}
        value={value}
        onChange={e => onChange(e.target.value)}
        rows={16}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500 text-white placeholder-gray-600 font-mono resize-none"
      />
      <div className="flex justify-between mt-2">
        <p className="text-xs text-gray-500">
          {value.length} characters
        </p>
        <p className="text-xs text-gray-500">
          ~{Math.ceil(value.split("SCENE").length - 1)} scenes
        </p>
      </div>
    </div>
  );
}