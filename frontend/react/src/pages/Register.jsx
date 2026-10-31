import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, UserRound, LockKeyhole, ArrowRight } from "lucide-react";
import toast from "react-hot-toast";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PrimaryButton from "../components/PrimaryButton";
import { useAuth } from "../context/AuthContext";
import { validateRegister } from "../lib/validation";

export default function Register() {
  const [values, setValues] = useState({ name: "", email: "", password: "", confirmPassword: "", acceptTerms: false });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  function update(e) {
    const { name, value, checked, type } = e.target;
    setValues(v => ({ ...v, [name]: type === "checkbox" ? checked : value }));
    setErrors(v => ({ ...v, [name]: "" }));
  }

  function submit(e) {
    e.preventDefault();
    const nextErrors = validateRegister(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setLoading(true);
    setTimeout(() => {
      register(values.name.trim(), values.email.trim());
      toast.success("Your demo account is ready!");
      navigate("/dashboard");
      setLoading(false);
    }, 450);
  }

  return (
    <AuthLayout eyebrow="START SOMETHING GREAT" title="Your next chapter starts here." description="Create a workspace that helps you and your team do your best work, every day.">
      <div className="mb-7">
        <p className="text-xs font-bold uppercase tracking-[.16em] text-indigo-600">Get started free</p>
        <h2 className="mt-2 font-['Manrope'] text-3xl font-extrabold tracking-tight text-slate-900">Create your account</h2>
        <p className="mt-2 text-sm text-slate-500">No credit card needed. Set up in less than a minute.</p>
      </div>
      <form onSubmit={submit} noValidate className="space-y-4">
        <FormField label="Full name" name="name" value={values.name} onChange={update} placeholder="Alex Morgan" autoComplete="name" icon={UserRound} error={errors.name} />
        <FormField label="Work email" name="email" type="email" value={values.email} onChange={update} placeholder="you@company.com" autoComplete="email" icon={Mail} error={errors.email} />
        <FormField label="Password" name="password" type="password" value={values.password} onChange={update} placeholder="Create a strong password" autoComplete="new-password" icon={LockKeyhole} error={errors.password} hint="At least 8 characters, including a letter and a number." />
        <FormField label="Confirm password" name="confirmPassword" type="password" value={values.confirmPassword} onChange={update} placeholder="Enter your password again" autoComplete="new-password" icon={LockKeyhole} error={errors.confirmPassword} />
        <div>
          <label className="flex items-start gap-2.5 text-xs leading-5 text-slate-600"><input name="acceptTerms" type="checkbox" checked={values.acceptTerms} onChange={update} className="mt-0.5 h-4 w-4 rounded border-slate-300 accent-indigo-600" /><span>I agree to the <a href="#terms" onClick={e => { e.preventDefault(); toast("Add your terms page link here."); }} className="font-bold text-indigo-600">Terms of Service</a> and <a href="#privacy" onClick={e => { e.preventDefault(); toast("Add your privacy policy link here."); }} className="font-bold text-indigo-600">Privacy Policy</a>.</span></label>
          {errors.acceptTerms && <p className="mt-1 text-xs text-rose-600">{errors.acceptTerms}</p>}
        </div>
        <PrimaryButton loading={loading}>Create account <ArrowRight size={17} /></PrimaryButton>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">Already have an account? <Link to="/signin" className="font-bold text-indigo-600 hover:text-indigo-700">Sign in</Link></p>
    </AuthLayout>
  );
}
