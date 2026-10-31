import { LoaderCircle } from "lucide-react";

export default function PrimaryButton({ children, loading = false, type = "submit", className = "", onClick }) {
  return (
    <button type={type} onClick={onClick} disabled={loading} className={`flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-70 ${className}`}>
      {loading && <LoaderCircle size={17} className="animate-spin" />}{children}
    </button>
  );
}
