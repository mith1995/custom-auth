import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, LockKeyhole } from "lucide-react";
import toast from "react-hot-toast";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PrimaryButton from "../components/PrimaryButton";
import { validateReset } from "../lib/validation";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [values, setValues] = useState({ password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const [complete, setComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function update(e) {
    setValues(v => ({ ...v, [e.target.name]: e.target.value }));
    setErrors(v => ({ ...v, [e.target.name]: "" }));
  }

  function submit(e) {
    e.preventDefault();
    const nextErrors = validateReset(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setLoading(true);
    // Demo-only: validate a real, expiring token on your backend before updating a password.
    setTimeout(() => { setComplete(true); setLoading(false); toast.success("Demo reset flow complete."); }, 500);
  }

  return (
    <AuthLayout eyebrow="SECURE YOUR ACCOUNT" title="A stronger password, a safer you." description="Choose a new password you haven’t used before to help keep your workspace protected.">
      <Link to="/signin" className="mb-8 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-indigo-600"><ArrowLeft size={16} /> Back to sign in</Link>
      {!complete ? <>
        <div className="mb-8">
          <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-indigo-50 text-indigo-600"><LockKeyhole size={25} /></div>
          <h2 className="font-['Manrope'] text-3xl font-extrabold tracking-tight text-slate-900">Reset password</h2>
          <p className="mt-3 text-sm leading-6 text-slate-500">Create a new password for your account. Use at least 8 characters, including a letter and a number.</p>
        </div>
        <form onSubmit={submit} noValidate className="space-y-5">
          <FormField label="New password" name="password" type="password" value={values.password} onChange={update} placeholder="Create a new password" autoComplete="new-password" icon={LockKeyhole} error={errors.password} />
          <FormField label="Confirm new password" name="confirmPassword" type="password" value={values.confirmPassword} onChange={update} placeholder="Enter it one more time" autoComplete="new-password" icon={LockKeyhole} error={errors.confirmPassword} />
          <PrimaryButton loading={loading}>Reset password</PrimaryButton>
        </form>
        {!token && <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">Demo page: a production app should require a valid reset token from the email link.</p>}
      </> : <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-6">
        <div className="grid h-12 w-12 place-items-center rounded-full bg-emerald-100 text-emerald-700"><CheckCircle2 size={24} /></div>
        <h2 className="mt-4 font-['Manrope'] text-2xl font-extrabold text-slate-900">Password updated</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">The demo reset flow is complete. Connect your backend to securely persist the new password.</p>
        <PrimaryButton type="button" className="mt-5" onClick={() => navigate("/signin")}>Go to sign in</PrimaryButton>
      </div>}
    </AuthLayout>
  );
}
