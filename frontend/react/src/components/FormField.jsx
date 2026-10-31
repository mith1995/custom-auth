import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";

export default function FormField({ label, type = "text", name, value, onChange, placeholder, error, autoComplete, required = true, hint, icon: Icon }) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === "password";
  const inputType = isPassword && showPassword ? "text" : type;
  return (
    <div>
      <label htmlFor={name} className="mb-2 block text-sm font-semibold text-slate-700">{label}</label>
      <div className="relative">
        {Icon && <Icon size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />}
        <input
          id={name} name={name} type={inputType} value={value} onChange={onChange}
          placeholder={placeholder} autoComplete={autoComplete} required={required}
          aria-invalid={Boolean(error)} aria-describedby={error ? `${name}-error` : hint ? `${name}-hint` : undefined}
          className={`input-focus w-full rounded-xl border bg-white py-3 text-sm text-slate-900 placeholder:text-slate-400 ${Icon ? "pl-10" : "pl-4"} ${isPassword ? "pr-11" : "pr-4"} ${error ? "border-rose-300" : "border-slate-200"} `}
        />
        {isPassword && <button type="button" onClick={() => setShowPassword(v => !v)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-700" aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>}
      </div>
      {error && <p id={`${name}-error`} className="mt-1.5 text-xs font-medium text-rose-600">{error}</p>}
      {!error && hint && <p id={`${name}-hint`} className="mt-1.5 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
