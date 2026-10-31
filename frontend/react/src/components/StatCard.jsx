import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export default function StatCard({ label, value, change, icon: Icon, color = "indigo", down = false }) {
  const colors = {
    indigo: "bg-indigo-50 text-indigo-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    sky: "bg-sky-50 text-sky-600",
  };
  const Trend = down ? ArrowDownRight : ArrowUpRight;
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft">
      <div className="flex items-center justify-between"><div className={`grid h-11 w-11 place-items-center rounded-xl ${colors[color]}`}><Icon size={20} /></div><span className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-bold ${down ? "bg-rose-50 text-rose-600" : "bg-emerald-50 text-emerald-700"}`}><Trend size={13} />{change}</span></div>
      <p className="mt-5 text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-1 font-['Manrope'] text-2xl font-extrabold tracking-tight text-slate-900">{value}</p>
    </div>
  );
}
