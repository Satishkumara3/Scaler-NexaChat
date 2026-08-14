"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { showToast } from "@/components/common/Toast";

type Step = "phone" | "otp" | "profile";

export default function RegisterPage() {
  const router = useRouter();
  const { requestRegisterOtp, register } = useAuth();

  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone.trim()) return;
    setError("");
    setLoading(true);
    try {
      await requestRegisterOtp(phone.trim());
      setStep("otp");
      showToast("OTP sent! Use 123456 in development.", "info");
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ?? "Failed to send OTP.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length < 6) return;
    setError("");
    setStep("profile");
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim()) return;
    setError("");
    setLoading(true);
    try {
      await register(phone.trim(), otp.trim(), displayName.trim());
      showToast("Account created! Welcome 🎉", "success");
      router.replace("/app");
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ?? "Registration failed. Please try again.";
      setError(msg);
      showToast(msg, "error");
      // If OTP was wrong, go back to OTP step
      if (msg.toLowerCase().includes("otp") || msg.toLowerCase().includes("invalid")) {
        setStep("otp");
        setOtp("");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      className="flex h-full items-center justify-center"
      style={{ backgroundColor: "var(--bg-primary)" }}
    >
      <div
        className="animate-fade-in w-full max-w-sm rounded-2xl p-8"
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border-color)",
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        }}
      >
        {/* Logo + title */}
        <div className="flex flex-col items-center mb-8 gap-3">
          <div
            className="rounded-full flex items-center justify-center"
            style={{ width: 64, height: 64, background: "var(--accent)" }}
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>

          {/* Step indicator */}
          <div className="flex gap-2">
            {(["phone", "otp", "profile"] as Step[]).map((s, i) => (
              <div
                key={s}
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor:
                    step === s
                      ? "var(--accent)"
                      : i < ["phone", "otp", "profile"].indexOf(step)
                      ? "var(--accent)"
                      : "var(--border-color)",
                  transition: "background-color var(--transition-base)",
                }}
              />
            ))}
          </div>

          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            {step === "phone" && "Create account"}
            {step === "otp" && "Verify number"}
            {step === "profile" && "Set up profile"}
          </h1>
          <p className="text-sm text-center" style={{ color: "var(--text-secondary)" }}>
            {step === "phone" && "Enter your phone number to get started"}
            {step === "otp" && `Enter the OTP sent to ${phone}`}
            {step === "profile" && "Choose a display name for your account"}
          </p>
        </div>

        {/* Step 1: Phone */}
        {step === "phone" && (
          <form onSubmit={handleRequestOtp} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="reg-phone"
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                Phone number
              </label>
              <input
                id="reg-phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91-9876543210"
                autoFocus
                style={{
                  backgroundColor: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: 10,
                  padding: "12px 14px",
                  color: "var(--text-primary)",
                  fontSize: 15,
                  outline: "none",
                }}
                onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.target.style.borderColor = "var(--border-color)")}
              />
            </div>
            {error && <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>}
            <button
              id="reg-request-otp-btn"
              type="submit"
              disabled={loading || !phone.trim()}
              style={{
                backgroundColor: loading || !phone.trim() ? "var(--bg-input)" : "var(--accent)",
                color: loading || !phone.trim() ? "var(--text-muted)" : "#fff",
                border: "none", borderRadius: 10, padding: "12px",
                fontSize: 15, fontWeight: 600,
                cursor: loading || !phone.trim() ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Sending…" : "Send OTP"}
            </button>
          </form>
        )}

        {/* Step 2: OTP */}
        {step === "otp" && (
          <form onSubmit={handleVerifyOtp} className="flex flex-col gap-4">
            <div
              className="text-center text-sm rounded-lg p-3"
              style={{
                backgroundColor: "rgba(0,168,132,0.1)",
                border: "1px solid rgba(0,168,132,0.3)",
                color: "var(--accent)",
              }}
            >
              🔑 Dev mode: OTP is <strong>123456</strong>
            </div>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="reg-otp"
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                OTP code
              </label>
              <input
                id="reg-otp"
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/, ""))}
                placeholder="123456"
                autoFocus
                style={{
                  backgroundColor: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: 10,
                  padding: "12px 14px",
                  color: "var(--text-primary)",
                  fontSize: 22,
                  letterSpacing: "0.3em",
                  textAlign: "center",
                  outline: "none",
                }}
                onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.target.style.borderColor = "var(--border-color)")}
              />
            </div>
            {error && <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>}
            <button
              id="reg-verify-otp-btn"
              type="submit"
              disabled={otp.length < 6}
              style={{
                backgroundColor: otp.length < 6 ? "var(--bg-input)" : "var(--accent)",
                color: otp.length < 6 ? "var(--text-muted)" : "#fff",
                border: "none", borderRadius: 10, padding: "12px",
                fontSize: 15, fontWeight: 600,
                cursor: otp.length < 6 ? "not-allowed" : "pointer",
              }}
            >
              Verify OTP
            </button>
            <button
              type="button"
              onClick={() => { setStep("phone"); setOtp(""); setError(""); }}
              className="text-sm"
              style={{ color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer" }}
            >
              ← Change phone number
            </button>
          </form>
        )}

        {/* Step 3: Profile */}
        {step === "profile" && (
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="reg-display-name"
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                Display name
              </label>
              <input
                id="reg-display-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="e.g. Satish Kumar"
                maxLength={50}
                autoFocus
                style={{
                  backgroundColor: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: 10,
                  padding: "12px 14px",
                  color: "var(--text-primary)",
                  fontSize: 15,
                  outline: "none",
                }}
                onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.target.style.borderColor = "var(--border-color)")}
              />
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                This is how other users will see you.
              </p>
            </div>
            {error && <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>}
            <button
              id="reg-submit-btn"
              type="submit"
              disabled={loading || displayName.trim().length < 2}
              style={{
                backgroundColor:
                  loading || displayName.trim().length < 2
                    ? "var(--bg-input)"
                    : "var(--accent)",
                color:
                  loading || displayName.trim().length < 2
                    ? "var(--text-muted)"
                    : "#fff",
                border: "none", borderRadius: 10, padding: "12px",
                fontSize: 15, fontWeight: 600,
                cursor:
                  loading || displayName.trim().length < 2
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              {loading ? "Creating account…" : "Create Account 🎉"}
            </button>
          </form>
        )}

        <p className="text-center mt-6 text-sm" style={{ color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link
            href="/login"
            style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 600 }}
          >
            Log in
          </Link>
        </p>
      </div>
    </main>
  );
}
