import { ArrowUpRight, CheckCircle2, Sparkles } from "lucide-react";
import Brand from "./Brand";

const benefits = [
  "One secure place for your work",
  "Simple workflows, less busywork",
  "Your team stays in sync",
];

export default function AuthLayout({ children, eyebrow = "WELCOME TO FLOWSPACE", title = "Make room for your best work.", description = "Bring your team, projects, and ideas together in one calm, focused workspace." }) {
  return (
    <main className="min-h-screen bg-white lg:grid lg:grid-cols-[minmax(360px,0.92fr)_1.08fr]">
      <aside className="auth-bg auth-grid relative hidden min-h-screen overflow-hidden px-10 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-14">
        <div className="absolute -right-28 top-44 h-80 w-80 rounded-full border border-white/10" />
        <div className="absolute -right-12 top-60 h-48 w-48 rounded-full border border-white/10" />
        <div className="relative z-10"><Brand light /></div>
        <div className="relative z-10 max-w-lg pb-8">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-semibold tracking-[.12em] text-indigo-200">
            <Sparkles size={14} /> {eyebrow}
          </div>
          <h1 className="font-['Manrope'] text-4xl font-extrabold leading-[1.14] tracking-tight xl:text-5xl">{title}</h1>
          <p className="mt-5 max-w-md text-base leading-7 text-slate-300">{description}</p>
          <div className="mt-9 space-y-3">
            {benefits.map((benefit) => <div key={benefit} className="flex items-center gap-3 text-sm text-slate-200"><CheckCircle2 size={17} className="text-emerald-300" />{benefit}</div>)}
          </div>
          <div className="mt-12 rounded-2xl border border-white/10 bg-white/[.06] p-5 backdrop-blur-sm">
            <div className="flex items-center gap-1 text-amber-300">★★★★★ <span className="ml-2 text-xs text-slate-300">4.9/5 from 2,000+ teams</span></div>
            <p className="mt-3 text-sm leading-6 text-slate-200">“Flowspace gave our team a little more clarity and a lot more momentum.”</p>
            <div className="mt-4 flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-pink-300 to-orange-300 text-xs font-bold text-slate-900">AM</div>
              <div><p className="text-sm font-semibold">Alex Morgan</p><p className="text-xs text-slate-400">Product lead, Northstar</p></div>
              <ArrowUpRight className="ml-auto text-slate-400" size={18} />
            </div>
          </div>
        </div>
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-400"><span>© 2026 Flowspace Inc.</span><div className="flex gap-5"><span>Privacy</span><span>Terms</span><span>Help</span></div></div>
      </aside>
      <section className="flex min-h-screen flex-col px-5 py-6 sm:px-10 lg:px-12 xl:px-20">
        <div className="lg:hidden"><Brand /></div>
        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[430px]">{children}</div>
        </div>
        <div className="flex justify-center gap-5 pb-1 text-xs text-slate-400 lg:justify-end"><span>Privacy policy</span><span>Terms of service</span><span>Need help?</span></div>
      </section>
    </main>
  );
}
