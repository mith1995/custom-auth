import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  UserRound,
  Camera,
  LockKeyhole,
  LogOut,
  Save,
  Mail,
  CalendarDays,
  Phone,
  X,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user, updateProfile, signOut } = useAuth();
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [activeTab, setActiveTab] = useState("profile");

  const [profile, setProfile] = useState({
    name: user?.name || "",
    email: user?.email || "",
    dob: user?.dob || "",
    phone: user?.phone || "",
    avatar: user?.avatar || "",
  });

  const [passwords, setPasswords] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const displayName =
    user?.name?.trim() || user?.email?.split("@")[0] || "there";

  const initials = (profile.name || "U")
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const handleProfileChange = (e) => {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value,
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image.");
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error("Image size must be below 2 MB.");
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      setProfile((prev) => ({
        ...prev,
        avatar: reader.result,
      }));
    };

    reader.readAsDataURL(file);
  };

  const handleSaveProfile = (e) => {
    e.preventDefault();

    if (profile.name.trim().length < 2) {
      toast.error("Please enter your full name.");
      return;
    }

    updateProfile({
      ...profile,
      name: profile.name.trim(),
    });

    toast.success("Profile updated successfully!");
  };

  const handleChangePassword = (e) => {
    e.preventDefault();

    if (!passwords.currentPassword) {
      toast.error("Enter your current password.");
      return;
    }

    if (
      passwords.newPassword.length < 8 ||
      !/[A-Za-z]/.test(passwords.newPassword) ||
      !/[0-9]/.test(passwords.newPassword)
    ) {
      toast.error("Password must contain 8 characters, a letter and a number.");
      return;
    }

    if (passwords.newPassword !== passwords.confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }

    toast.error(
      "Connect the password-change API to update your password securely.",
    );
  };

  const handleSignOut = () => {
    signOut();
    navigate("/signin", { replace: true });
  };

  const tabs = [
    { id: "profile", label: "General Details", icon: UserRound },
    { id: "password", label: "Change Password", icon: LockKeyhole },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-indigo-600">
              Flowspace
            </h1>
            <p className="text-xs text-slate-500">Your personal account</p>
          </div>

          <button
            type="button"
            onClick={handleSignOut}
            className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
          >
            <LogOut size={17} />
            Sign Out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        {/* Welcome Message */}
        <section className="mb-8 rounded-3xl bg-gradient-to-r from-indigo-600 to-violet-600 p-7 text-white shadow-lg sm:p-10">
          <p className="text-sm font-medium text-indigo-200">YOUR ACCOUNT</p>

          <h2 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
            Welcome, {displayName}!
          </h2>

          <p className="mt-3 max-w-lg text-sm leading-6 text-indigo-100 sm:text-base">
            Manage your personal details and keep your account information up to
            date.
          </p>
        </section>

        {/* Profile Summary */}
        <section className="mb-6 flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full bg-indigo-100 text-xl font-bold text-indigo-700">
            {profile.avatar ? (
              <img
                src={profile.avatar}
                alt="Profile"
                className="h-full w-full object-cover"
              />
            ) : (
              initials
            )}
          </div>

          <div className="min-w-0">
            <h3 className="truncate font-bold text-slate-900">{displayName}</h3>
            <p className="truncate text-sm text-slate-500">{user?.email}</p>
            <p className="mt-1 text-xs text-emerald-600">Personal account</p>
          </div>
        </section>

        {/* Settings Tabs */}
        <div className="mb-6 flex flex-wrap gap-2">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                activeTab === id
                  ? "bg-indigo-600 text-white shadow-md"
                  : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </div>

        {/* General Details */}
        {activeTab === "profile" && (
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 py-5">
              <h3 className="text-lg font-bold text-slate-900">
                Personal Information
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Update your profile photo and personal details.
              </p>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-6 p-6 sm:p-8">
              {/* Profile Picture */}
              <div className="flex flex-wrap items-center gap-4">
                <div className="relative flex h-20 w-20 items-center justify-center overflow-hidden rounded-full bg-indigo-100 text-xl font-bold text-indigo-700">
                  {profile.avatar ? (
                    <img
                      src={profile.avatar}
                      alt="Profile preview"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    initials
                  )}

                  <button
                    type="button"
                    onClick={() => fileRef.current?.click()}
                    aria-label="Upload profile picture"
                    className="absolute bottom-0 right-0 rounded-full bg-indigo-600 p-2 text-white hover:bg-indigo-700"
                  >
                    <Camera size={15} />
                  </button>

                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleImageChange}
                  />
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    Profile Picture
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    PNG or JPG, maximum 2 MB
                  </p>

                  {profile.avatar && (
                    <button
                      type="button"
                      onClick={() =>
                        setProfile((prev) => ({
                          ...prev,
                          avatar: "",
                        }))
                      }
                      className="mt-2 flex items-center gap-1 text-xs font-semibold text-red-600"
                    >
                      <X size={13} />
                      Remove picture
                    </button>
                  )}
                </div>
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                <FormInput
                  label="Full Name"
                  name="name"
                  value={profile.name}
                  onChange={handleProfileChange}
                  placeholder="Enter your full name"
                  icon={UserRound}
                />

                <FormInput
                  label="Email Address"
                  name="email"
                  type="email"
                  value={profile.email}
                  onChange={() => {}}
                  icon={Mail}
                  disabled
                />

                <FormInput
                  label="Date of Birth"
                  name="dob"
                  type="date"
                  value={profile.dob}
                  onChange={handleProfileChange}
                  icon={CalendarDays}
                />

                <FormInput
                  label="Phone Number"
                  name="phone"
                  type="tel"
                  value={profile.phone}
                  onChange={handleProfileChange}
                  placeholder="Enter phone number"
                  icon={Phone}
                />
              </div>

              <div className="flex justify-end border-t border-slate-100 pt-5">
                <button
                  type="submit"
                  className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-indigo-700"
                >
                  <Save size={17} />
                  Save Changes
                </button>
              </div>
            </form>
          </section>
        )}

        {/* Change Password */}
        {activeTab === "password" && (
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 py-5">
              <h3 className="text-lg font-bold text-slate-900">
                Change Password
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Choose a strong password for your account.
              </p>
            </div>

            <form
              onSubmit={handleChangePassword}
              className="max-w-2xl space-y-5 p-6 sm:p-8"
            >
              <FormInput
                label="Current Password"
                name="currentPassword"
                type="password"
                value={passwords.currentPassword}
                onChange={(e) =>
                  setPasswords({
                    ...passwords,
                    currentPassword: e.target.value,
                  })
                }
                placeholder="Enter current password"
              />

              <FormInput
                label="New Password"
                name="newPassword"
                type="password"
                value={passwords.newPassword}
                onChange={(e) =>
                  setPasswords({
                    ...passwords,
                    newPassword: e.target.value,
                  })
                }
                placeholder="At least 8 characters"
              />

              <FormInput
                label="Confirm New Password"
                name="confirmPassword"
                type="password"
                value={passwords.confirmPassword}
                onChange={(e) =>
                  setPasswords({
                    ...passwords,
                    confirmPassword: e.target.value,
                  })
                }
                placeholder="Re-enter new password"
              />

              <p className="rounded-xl bg-amber-50 p-4 text-xs leading-5 text-amber-800">
                Password changes require backend verification. Connect this form
                to your Django API before using it with real accounts.
              </p>

              <div className="border-t border-slate-100 pt-5">
                <button
                  type="submit"
                  className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white hover:bg-indigo-700"
                >
                  Update Password
                </button>
              </div>
            </form>
          </section>
        )}
      </main>
    </div>
  );
}

function FormInput({
  label,
  name,
  type = "text",
  value,
  onChange,
  placeholder,
  icon: Icon,
  disabled = false,
}) {
  return (
    <div>
      <label
        htmlFor={name}
        className="mb-2 block text-sm font-semibold text-slate-700"
      >
        {label}
      </label>

      <div className="relative">
        {Icon && (
          <Icon
            size={17}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
          />
        )}

        <input
          id={name}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          max={
            type === "date" ? new Date().toISOString().slice(0, 10) : undefined
          }
          className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500"
        />
      </div>
    </div>
  );
}
