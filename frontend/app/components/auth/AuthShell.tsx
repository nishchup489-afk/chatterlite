import Link from "next/link";
import type { ReactNode } from "react";

type AuthMode = "sign-in" | "sign-up";

export default function AuthShell({
  mode,
  children,
}: {
  mode: AuthMode;
  children: ReactNode;
}) {
  const isSignIn = mode === "sign-in";

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#020617] text-[#eafaff]">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(56,189,248,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(56,189,248,0.04)_1px,transparent_1px)] bg-size-[64px_64px]" />

      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(34,211,238,0.12),transparent_380px),linear-gradient(180deg,#020617_0%,#07142f_100%)]" />

      <Link
        href="/"
        className="absolute left-7 top-9 z-10 flex items-center gap-3 text-[17px] font-extrabold tracking-[-0.03em]"
      >
        <span className="h-2.5 w-2.5 rounded-full bg-[#39dff3] shadow-[0_0_18px_rgba(57,223,243,0.9)]" />
        <span>ChatterLite</span>
      </Link>

      <section className="relative z-10 flex min-h-dvh items-center justify-center px-5 py-24">
        <div className="w-full max-w-95">
          <div className="mb-9 grid h-12.5 grid-cols-2 rounded-[14px] border border-cyan-400/25 bg-[#031126]/85 p-1 backdrop-blur">
            <Link
              href="/sign-in"
              className={[
                "flex items-center justify-center rounded-xl text-sm font-bold transition",
                isSignIn
                  ? "border border-cyan-400/50 bg-cyan-400/15 text-[#5deaff] shadow-[0_0_28px_rgba(34,211,238,0.22)]"
                  : "text-slate-500 hover:text-cyan-100",
              ].join(" ")}
            >
              Sign In
            </Link>

            <Link
              href="/sign-up"
              className={[
                "flex items-center justify-center rounded-xl text-sm font-bold transition",
                !isSignIn
                  ? "border border-cyan-400/50 bg-cyan-400/15 text-[#5deaff] shadow-[0_0_28px_rgba(34,211,238,0.22)]"
                  : "text-slate-500 hover:text-cyan-100",
              ].join(" ")}
            >
              Sign Up
            </Link>
          </div>

          {children}

          <p className="mt-8 text-center font-mono text-[11px] tracking-wider text-slate-700">
            Secured by Clerk · authenticated WebSocket sessions
          </p>
        </div>
      </section>
    </main>
  );
}