import { useState } from "react";
import {
  Bell,
  ChevronDown,
  CircleHelp,
  Command,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Menu,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  ShoppingBag,
  Users,
  X,
  TrendingUp,
  Wallet,
  Clock3,
  CheckCircle2,
  ArrowUpRight,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import Brand from "../components/Brand";
import StatCard from "../components/StatCard";

const navItems = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Projects", icon: ShoppingBag, count: "8" },
  { label: "Team", icon: Users },
  { label: "Billing", icon: CreditCard },
];
const activity = [
  {
    initials: "JD",
    color: "bg-violet-100 text-violet-700",
    title: "Jordan Davis",
    detail: "commented on Website redesign",
    time: "12 min ago",
    tag: "Comment",
  },
  {
    initials: "SK",
    color: "bg-amber-100 text-amber-700",
    title: "Sam Kim",
    detail: "completed Mobile app wireframes",
    time: "48 min ago",
    tag: "Completed",
  },
  {
    initials: "AL",
    color: "bg-emerald-100 text-emerald-700",
    title: "Avery Lee",
    detail: "created a new project brief",
    time: "2 hours ago",
    tag: "Created",
  },
  {
    initials: "MR",
    color: "bg-sky-100 text-sky-700",
    title: "Morgan Reed",
    detail: "uploaded 4 new design assets",
    time: "3 hours ago",
    tag: "Upload",
  },
];
const projects = [
  {
    name: "Website redesign",
    type: "Design",
    progress: 78,
    people: ["JD", "SK", "AM"],
    due: "Oct 18",
    color: "bg-indigo-500",
  },
  {
    name: "Mobile app launch",
    type: "Product",
    progress: 52,
    people: ["AL", "MR", "JD"],
    due: "Oct 24",
    color: "bg-sky-500",
  },
  {
    name: "Brand guidelines",
    type: "Marketing",
    progress: 34,
    people: ["AM", "SK"],
    due: "Oct 30",
    color: "bg-amber-500",
  },
];

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeNav, setActiveNav] = useState("Overview");
  const [search, setSearch] = useState("");

  function logout() {
    signOut();
    toast.success("You’ve signed out.");
    navigate("/signin", { replace: true });
  }

  const firstName = user?.name?.split(" ")[0] || "there";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {sidebarOpen && (
        <button
          aria-label="Close navigation overlay"
          className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col border-r border-slate-200 bg-white px-5 py-6 transition-transform duration-300 lg:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center justify-between px-1">
          <Brand />
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 lg:hidden"
          >
            <X size={19} />
          </button>
        </div>
        <button
          onClick={() =>
            toast.success("New project dialog is ready to connect.")
          }
          className="mt-9 flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700"
        >
          <Plus size={17} /> Create new project
        </button>
        <p className="mb-3 mt-9 px-3 text-[11px] font-bold uppercase tracking-[.15em] text-slate-400">
          Workspace
        </p>
        <nav className="space-y-1">
          {navItems.map(({ label, icon: Icon, count }) => (
            <button
              key={label}
              onClick={() => {
                setActiveNav(label);
                setSidebarOpen(false);
                if (label !== "Overview")
                  toast(`${label} section is a UI placeholder.`);
              }}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${activeNav === label ? "bg-indigo-50 text-indigo-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`}
            >
              <Icon size={18} />
              <span>{label}</span>
              {count && (
                <span className="ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                  {count}
                </span>
              )}
              {activeNav === label && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-600" />
              )}
            </button>
          ))}
        </nav>
        <p className="mb-3 mt-9 px-3 text-[11px] font-bold uppercase tracking-[.15em] text-slate-400">
          Preferences
        </p>
        <button
          onClick={() => toast("Settings page can be added next.")}
          className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
        >
          <Settings size={18} /> Settings
        </button>
        <button
          onClick={() => toast("Help center link can be configured here.")}
          className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
        >
          <CircleHelp size={18} /> Help center
        </button>
        <div className="mt-auto rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 p-4 text-white">
          <div className="flex items-center gap-2 text-sm font-bold">
            <Command size={17} /> Upgrade your plan
          </div>
          <p className="mt-2 text-xs leading-5 text-indigo-100">
            Unlock unlimited projects and advanced team insights.
          </p>
          <button
            onClick={() => toast("Upgrade flow is a demo placeholder.")}
            className="mt-3 w-full rounded-lg bg-white px-3 py-2 text-xs font-bold text-indigo-700 transition hover:bg-indigo-50"
          >
            Explore plans <ArrowUpRight className="ml-1 inline" size={13} />
          </button>
        </div>
        <button
          onClick={logout}
          className="mt-5 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-rose-50 hover:text-rose-600"
        >
          <LogOut size={18} /> Sign out
        </button>
      </aside>

      <div className="min-h-screen lg:pl-[260px]">
        <header className="sticky top-0 z-20 flex h-[76px] items-center gap-4 border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-xl sm:px-7 lg:px-9">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
          >
            <Menu size={20} />
          </button>
          <div className="relative hidden max-w-md flex-1 sm:block">
            <Search
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
              size={17}
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search anything..."
              className="input-focus w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm placeholder:text-slate-400"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] text-slate-400">
              ⌘ K
            </kbd>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={() => toast("You're all caught up!")}
              className="relative rounded-xl p-2.5 text-slate-500 hover:bg-slate-100"
            >
              <Bell size={19} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full border-2 border-white bg-rose-500" />
            </button>
            <div className="hidden h-8 w-px bg-slate-200 sm:block" />
            <button
              onClick={() =>
                toast("Account menu: profile, preferences, and sign out.")
              }
              className="flex items-center gap-2.5 rounded-xl p-1.5 transition hover:bg-slate-50"
            >
              <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-xs font-extrabold text-white">
                {(user?.name || "FS")
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .slice(0, 2)
                  .toUpperCase()}
              </div>
              <div className="hidden text-left sm:block">
                <p className="max-w-32 truncate text-sm font-bold text-slate-800">
                  {user?.name || "Flowspace User"}
                </p>
                <p className="text-xs text-slate-400">Free plan</p>
              </div>
              <ChevronDown
                size={15}
                className="hidden text-slate-400 sm:block"
              />
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-[1500px] px-4 py-7 sm:px-7 lg:px-9 lg:py-9">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-400">
                <span>Workspace</span>
                <span>/</span>
                <span className="text-indigo-600">Overview</span>
              </div>
              <h1 className="font-['Manrope'] text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
                Good afternoon, {firstName} <span>✦</span>
              </h1>
              <p className="mt-2 text-sm text-slate-500">
                Here’s what’s happening with your projects today.
              </p>
            </div>
            <button
              onClick={() =>
                toast.success("Your report is being prepared (demo).")
              }
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <TrendingUp size={16} /> Export report
            </button>
          </div>

          <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Total projects"
              value="24"
              change="+12.8%"
              icon={ShoppingBag}
              color="indigo"
            />
            <StatCard
              label="Team members"
              value="12"
              change="+4.2%"
              icon={Users}
              color="sky"
            />
            <StatCard
              label="Tasks completed"
              value="184"
              change="+18.6%"
              icon={CheckCircle2}
              color="emerald"
            />
            <StatCard
              label="Hours tracked"
              value="326.5"
              change="-2.4%"
              icon={Clock3}
              color="amber"
              down
            />
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_1fr]">
            <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-['Manrope'] text-base font-extrabold text-slate-900">
                    Project progress
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Track your team’s active work
                  </p>
                </div>
                <button
                  onClick={() => toast("Project list is a demo placeholder.")}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100"
                >
                  <MoreHorizontal size={20} />
                </button>
              </div>
              <div className="mt-5 space-y-5">
                {projects
                  .filter((p) =>
                    p.name.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map((project) => (
                    <div key={project.name}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex min-w-0 items-center gap-3">
                          <span
                            className={`h-9 w-1 rounded-full ${project.color}`}
                          />
                          <div className="min-w-0">
                            <p className="truncate text-sm font-bold text-slate-800">
                              {project.name}
                            </p>
                            <p className="mt-0.5 text-xs text-slate-400">
                              {project.type} · Due {project.due}
                            </p>
                          </div>
                        </div>
                        <span className="text-sm font-extrabold text-slate-700">
                          {project.progress}%
                        </span>
                      </div>
                      <div className="ml-4 mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full rounded-full ${project.color} transition-all`}
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                      <div className="ml-4 mt-2 flex items-center justify-between">
                        <div className="flex -space-x-2">
                          {project.people.map((person, i) => (
                            <span
                              key={person + i}
                              className="grid h-7 w-7 place-items-center rounded-full border-2 border-white bg-slate-100 text-[9px] font-extrabold text-slate-600"
                            >
                              {person}
                            </span>
                          ))}
                        </div>
                        <span className="text-[11px] font-medium text-slate-400">
                          {project.people.length} members
                        </span>
                      </div>
                    </div>
                  ))}
                {projects.filter((p) =>
                  p.name.toLowerCase().includes(search.toLowerCase()),
                ).length === 0 && (
                  <p className="py-8 text-center text-sm text-slate-400">
                    No projects match “{search}”.
                  </p>
                )}
              </div>
              <button
                onClick={() => {
                  setActiveNav("Projects");
                  toast("Projects page is ready to build next.");
                }}
                className="mt-6 w-full rounded-xl border border-slate-200 py-2.5 text-sm font-bold text-slate-600 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
              >
                View all projects
              </button>
            </section>

            <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-['Manrope'] text-base font-extrabold text-slate-900">
                    Recent activity
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Latest updates from your team
                  </p>
                </div>
                <button
                  onClick={() => toast("Showing the latest team activity.")}
                  className="text-xs font-bold text-indigo-600 hover:text-indigo-700"
                >
                  View all
                </button>
              </div>
              <div className="mt-4 divide-y divide-slate-100">
                {activity.map((item) => (
                  <div
                    key={item.title}
                    className="flex gap-3 py-4 first:pt-2 last:pb-1"
                  >
                    <div
                      className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-[10px] font-extrabold ${item.color}`}
                    >
                      {item.initials}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm leading-5 text-slate-700">
                        <span className="font-bold">{item.title}</span>{" "}
                        {item.detail}
                      </p>
                      <div className="mt-1.5 flex items-center gap-2">
                        <span className="text-[11px] text-slate-400">
                          {item.time}
                        </span>
                        <span className="h-1 w-1 rounded-full bg-slate-300" />
                        <span className="text-[11px] font-semibold text-indigo-600">
                          {item.tag}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm lg:col-span-2 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-['Manrope'] text-base font-extrabold text-slate-900">
                    Your week at a glance
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Task completions over the last 7 days
                  </p>
                </div>
                <span className="rounded-lg bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-500">
                  This week <ChevronDown className="ml-1 inline" size={13} />
                </span>
              </div>
              <div className="mt-7 flex h-36 items-end justify-between gap-2 sm:gap-4">
                {[
                  { d: "Mon", h: 48, n: 12 },
                  { d: "Tue", h: 70, n: 18 },
                  { d: "Wed", h: 55, n: 14 },
                  { d: "Thu", h: 88, n: 23 },
                  { d: "Fri", h: 64, n: 17 },
                  { d: "Sat", h: 36, n: 9 },
                  { d: "Sun", h: 76, n: 20 },
                ].map((day) => (
                  <div
                    key={day.d}
                    className="flex h-full flex-1 flex-col items-center justify-end gap-2"
                  >
                    <span className="text-[10px] font-bold text-slate-400">
                      {day.n}
                    </span>
                    <div
                      className="flex w-full max-w-10 items-end overflow-hidden rounded-t-lg bg-indigo-50"
                      style={{ height: `${day.h}%` }}
                    >
                      <div
                        className="w-full rounded-t-lg bg-gradient-to-t from-indigo-600 to-violet-400 transition-all hover:opacity-80"
                        style={{ height: `${Math.max(45, day.h)}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-medium text-slate-400">
                      {day.d}
                    </span>
                  </div>
                ))}
              </div>
            </section>
            <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-violet-50 text-violet-600">
                <Wallet size={20} />
              </div>
              <h2 className="mt-4 font-['Manrope'] text-base font-extrabold text-slate-900">
                Workspace usage
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Your free plan this month
              </p>
              <div className="mt-5 flex items-end justify-between">
                <span className="text-2xl font-extrabold text-slate-900">
                  7.2 GB
                </span>
                <span className="text-xs font-semibold text-slate-400">
                  of 10 GB
                </span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full w-[72%] rounded-full bg-violet-500" />
              </div>
              <p className="mt-3 text-xs leading-5 text-slate-500">
                You’ve used 72% of your available storage. Upgrade for more
                room.
              </p>
              <button
                onClick={() => toast("Plan comparison is a demo placeholder.")}
                className="mt-4 text-sm font-bold text-indigo-600 hover:text-indigo-700"
              >
                Compare plans <ArrowUpRight className="ml-1 inline" size={14} />
              </button>
            </section>
          </div>
          <footer className="mt-9 flex flex-col gap-2 border-t border-slate-200 pt-5 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
            <span>© 2026 Flowspace. Made for focused teams.</span>
            <span className="flex gap-4">
              <a
                href="#status"
                onClick={(e) => {
                  e.preventDefault();
                  toast("All systems operational (demo).");
                }}
                className="hover:text-slate-600"
              >
                System status
              </a>
              <a
                href="#docs"
                onClick={(e) => {
                  e.preventDefault();
                  toast("Documentation link can be configured.");
                }}
                className="hover:text-slate-600"
              >
                Documentation
              </a>
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}
