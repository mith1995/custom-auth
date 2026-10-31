import { Layers3 } from "lucide-react";

export default function Brand({ light = false }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-500 text-white shadow-lg shadow-indigo-500/30">
        <Layers3 size={21} strokeWidth={2.4} />
      </div>
      <span className={`font-['Manrope'] text-xl font-extrabold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>
        flowspace<span className="text-indigo-400">.</span>
      </span>
    </div>
  );
}
