"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { showToast } from "@/components/common/Toast";

type Step = "phone" | "otp";

export default function LoginPage() {
  const router = useRouter();
  const { requestLoginOtp, login } = useAuth();

  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone.trim()) return;
    setError("");
    setLoading(true);
    try {
      await requestLoginOtp(phone.trim());
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
    if (!otp.trim()) return;
    setError("");
    setLoading(true);
    try {
      await login(phone.trim(), otp.trim());
      showToast("Welcome back!", "success");
      router.replace("/app");
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ?? "Invalid OTP. Please try again.";
      setError(msg);
      showToast(msg, "error");
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
        {/* Logo */}
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
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Welcome back
          </h1>
          <p className="text-sm text-center" style={{ color: "var(--text-secondary)" }}>
            {step === "phone"
              ? "Enter your phone number to continue"
              : `Enter the OTP sent to ${phone}`}
          </p>
        </div>

        {/* Phone step */}
        {step === "phone" && (
          <form onSubmit={handleRequestOtp} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="login-phone"
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                Phone number
              </label>
              <input
                id="login-phone"
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
                  transition: "border-color var(--transition-fast)",
                }}
                onFocus={(e) =>
                  (e.target.style.borderColor = "var(--accent)")
                }
                onBlur={(e) =>
                  (e.target.style.borderColor = "var(--border-color)")
                }
              />
            </div>
            {error && (
              <p className="text-sm" style={{ color: "#ef4444" }}>
                {error}
              </p>
            )}
            <button
              id="login-request-otp-btn"
              type="submit"
              disabled={loading || !phone.trim()}
              style={{
                backgroundColor: loading || !phone.trim() ? "var(--bg-input)" : "var(--accent)",
                color: loading || !phone.trim() ? "var(--text-muted)" : "#fff",
                border: "none",
                borderRadius: 10,
                padding: "12px",
                fontSize: 15,
                fontWeight: 600,
                cursor: loading || !phone.trim() ? "not-allowed" : "pointer",
                transition: "background-color var(--transition-fast)",
              }}
            >
              {loading ? "Sending…" : "Send OTP"}
            </button>
          </form>
        )}

        {/* OTP step */}
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
                htmlFor="login-otp"
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                OTP code
              </label>
              <input
                id="login-otp"
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
                onFocus={(e) =>
                  (e.target.style.borderColor = "var(--accent)")
                }
                onBlur={(e) =>
                  (e.target.style.borderColor = "var(--border-color)")
                }
              />
            </div>
            {error && (
              <p className="text-sm" style={{ color: "#ef4444" }}>
                {error}
              </p>
            )}
            <button
              id="login-verify-otp-btn"
              type="submit"
              disabled={loading || otp.length < 6}
              style={{
                backgroundColor: loading || otp.length < 6 ? "var(--bg-input)" : "var(--accent)",
                color: loading || otp.length < 6 ? "var(--text-muted)" : "#fff",
                border: "none",
                borderRadius: 10,
                padding: "12px",
                fontSize: 15,
                fontWeight: 600,
                cursor: loading || otp.length < 6 ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Verifying…" : "Log In"}
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

        <p className="text-center mt-6 text-sm" style={{ color: "var(--text-muted)" }}>
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 600 }}
          >
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}
