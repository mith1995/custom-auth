import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Mail, LockKeyhole, ArrowRight, Github } from "lucide-react";
import toast from "react-hot-toast";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PrimaryButton from "../components/PrimaryButton";
import { useAuth } from "../context/AuthContext";
import { validateSignIn } from "../lib/validation";

export default function SignIn() {
  const [values, setValues] = useState({ email: "", password: "", remember: true });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function update(e) {
    const { name, value, checked, type } = e.target;
    setValues(v => ({ ...v, [name]: type === "checkbox" ? checked : value }));
    setErrors(v => ({ ...v, [name]: "" }));
  }

  function submit(e) {
    e.preventDefault();
    const nextErrors = validateSignIn(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setLoading(true);
    setTimeout(() => {
      signIn(values.email, values.password);
      toast.success("Welcome back!");
      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
      setLoading(false);
    }, 450);
  }

  return (
    <AuthLayout eyebrow="YOUR WORKSPACE AWAITS" title="Good to see you again." description="Sign in to pick up where you left off and keep your best work moving forward.">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-[.16em] text-indigo-600">Sign in</p>
        <h2 className="mt-2 font-['Manrope'] text-3xl font-extrabold tracking-tight text-slate-900">Welcome back</h2>
        <p className="mt-2 text-sm text-slate-500">Enter your details to access your workspace.</p>
      </div>
      <form onSubmit={submit} noValidate className="space-y-5">
        <FormField label="Email address" name="email" type="email" value={values.email} onChange={update} placeholder="you@company.com" autoComplete="email" icon={Mail} error={errors.email} />
        <div>
          <div className="mb-2 flex items-center justify-between"><label htmlFor="password" className="text-sm font-semibold text-slate-700">Password</label><Link to="/forgot-password" className="text-xs font-bold text-indigo-600 hover:text-indigo-700">Forgot password?</Link></div>
          <FormField label="" name="password" type="password" value={values.password} onChange={update} placeholder="Enter your password" autoComplete="current-password" icon={LockKeyhole} error={errors.password} />
        </div>
        <label className="flex cursor-pointer items-center gap-2.5 text-sm text-slate-600"><input name="remember" type="checkbox" checked={values.remember} onChange={update} className="h-4 w-4 rounded border-slate-300 accent-indigo-600" />Keep me signed in</label>
        <PrimaryButton loading={loading}>Sign in <ArrowRight size={17} /></PrimaryButton>
      </form>
      <div className="my-6 flex items-center gap-4"><div className="h-px flex-1 bg-slate-200" /><span className="text-xs text-slate-400">OR CONTINUE WITH</span><div className="h-px flex-1 bg-slate-200" /></div>
      <button type="button" onClick={() => toast("Connect Google OAuth to enable social sign-in.", { icon: "ℹ️" })} className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"><GoogleMark /> Continue with Google</button>
      <p className="mt-7 text-center text-sm text-slate-500">New to Flowspace? <Link to="/register" className="font-bold text-indigo-600 hover:text-indigo-700">Create an account</Link></p>
      <p className="mt-8 rounded-xl bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-500"><strong className="text-slate-700">Demo note:</strong> This starter uses local demo authentication. Use any valid email and a non-empty password to explore the dashboard.</p>
    </AuthLayout>
  );
}

function GoogleMark() {
  return <svg viewBox="0 0 48 48" className="h-4 w-4" aria-hidden="true"><path fill="#FFC107" d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.8h11a9.4 9.4 0 0 1-4.1 6.2v5.1h6.6c3.9-3.6 6.1-8.9 6.1-15Z"/><path fill="#FF3D00" d="M24 44c5.5 0 10.1-1.8 13.5-4.9l-6.6-5.1c-1.8 1.2-4 2-6.9 2-5.3 0-9.8-3.6-11.4-8.4H5.8v5.3A20 20 0 0 0 24 44Z"/><path fill="#4CAF50" d="M12.6 27.6a12 12 0 0 1 0-7.2v-5.3H5.8a20 20 0 0 0 0 17.8l6.8-5.3Z"/><path fill="#1976D2" d="M24 12c3 0 5.7 1 7.8 3l5.8-5.8C34.1 5.9 29.5 4 24 4A20 20 0 0 0 5.8 15.1l6.8 5.3C14.2 15.6 18.7 12 24 12Z"/></svg>;
}
