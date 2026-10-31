import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Mail, Send } from "lucide-react";
import toast from "react-hot-toast";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PrimaryButton from "../components/PrimaryButton";
import { emailIsValid } from "../lib/validation";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  function submit(e) {
    e.preventDefault();
    if (!emailIsValid(email)) { setError("Enter a valid email address."); return; }
    setError("");
    setLoading(true);
    // Demo flow only. A real app should request a single-use token from its backend.
    setTimeout(() => { setSent(true); setLoading(false); toast.success("If the account exists, a reset link has been requested."); }, 500);
  }

  return (
    <AuthLayout eyebrow="ACCOUNT RECOVERY" title="A fresh start is one email away." description="It happens to everyone. We’ll help you get back into your workspace securely.">
      <Link to="/signin" className="mb-8 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-indigo-600"><ArrowLeft size={16} /> Back to sign in</Link>
      {!sent ? <>
        <div className="mb-8">
          <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-indigo-50 text-indigo-600"><Mail size={25} /></div>
          <h2 className="font-['Manrope'] text-3xl font-extrabold tracking-tight text-slate-900">Forgot password?</h2>
          <p className="mt-3 text-sm leading-6 text-slate-500">Enter the email address associated with your account. If it exists, we’ll send instructions to reset your password.</p>
        </div>
        <form onSubmit={submit} noValidate className="space-y-5">
          <FormField label="Email address" name="email" type="email" value={email} onChange={e => { setEmail(e.target.value); setError(""); }} placeholder="you@company.com" autoComplete="email" icon={Mail} error={error} />
          <PrimaryButton loading={loading}>Send reset link <Send size={16} /></PrimaryButton>
        </form>
      </> : <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-6">
        <div className="grid h-12 w-12 place-items-center rounded-full bg-emerald-100 text-emerald-700"><Mail size={23} /></div>
        <h2 className="mt-4 font-['Manrope'] text-2xl font-extrabold text-slate-900">Check your inbox</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">If an account is associated with <strong>{email}</strong>, you’ll receive a password reset link shortly.</p>
        <button onClick={() => { setSent(false); toast("You can request another link."); }} className="mt-5 text-sm font-bold text-indigo-600 hover:text-indigo-700">Try another email</button>
      </div>}
      <p className="mt-8 text-center text-sm text-slate-500">Remember your password? <Link to="/signin" className="font-bold text-indigo-600">Sign in</Link></p>
    </AuthLayout>
  );
}
