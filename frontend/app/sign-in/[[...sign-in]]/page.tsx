"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useSignIn } from "@clerk/nextjs";

import AuthShell from "@/app/components/auth/AuthShell";

type ClerkLikeError = {
  errors?: Array<{
    message?: string;
    code?: string;
  }>;
};

function getClerkErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "errors" in error) {
    const clerkError = error as ClerkLikeError;
    return clerkError.errors?.[0]?.message ?? "Something went wrong.";
  }

  return "Something went wrong. Try again.";
}

export default function SignInPage() {
  const { signIn, errors, fetchStatus } = useSignIn();

  const [emailAddress, setEmailAddress] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");

  const isLoading = fetchStatus === "fetching";

  async function finalizeSignIn() {
    await signIn.finalize({
      navigate: ({ session, decorateUrl }) => {
        if (session?.currentTask) {
          console.log(session.currentTask);
          return;
        }

        window.location.href = decorateUrl("/dashboard");
      },
    });
  }

  async function handleGoogleSignIn() {
    setLocalError("");

    const { error } = await signIn.sso({
      strategy: "oauth_google",
      redirectCallbackUrl: "/sso-callback",
      redirectUrl: "/dashboard",
    });

    if (error) {
      setLocalError(getClerkErrorMessage(error));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");

    const { error } = await signIn.password({
      emailAddress,
      password,
    });

    if (error) {
      setLocalError(getClerkErrorMessage(error));
      return;
    }

    if (signIn.status === "complete") {
      await finalizeSignIn();
      return;
    }

    if (signIn.status === "needs_client_trust") {
      setLocalError("Extra email verification is required. We will add that flow next.");
      return;
    }

    if (signIn.status === "needs_second_factor") {
      setLocalError("MFA is required. We will add that flow later.");
      return;
    }

    setLocalError("Sign in is not complete yet.");
  }

  const fields = errors.fields as any;

  const errorMessage =
    localError ||
    fields?.emailAddress?.message ||
    fields?.password?.message ||
    errors.global?.[0]?.message;

  return (
    <AuthShell mode="sign-in">
      <div className="mb-7">
        <h1 className="text-[28px] font-extrabold leading-none tracking-[-0.04em] text-[#eafaff]">
          Welcome back
        </h1>

        <p className="mt-4 text-[15px] leading-6 text-[#8793aa]">
          Sign in to reconnect to your rooms and threads.
        </p>
      </div>

      <button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={isLoading}
        className="flex h-11 w-full items-center justify-center gap-3 rounded-xl border border-cyan-400/25 bg-[#02091c] text-sm font-bold text-[#eafaff] transition hover:border-cyan-300/45 hover:bg-[#06162c] disabled:cursor-not-allowed disabled:opacity-70"
      >
        <span className="font-black text-[#47dff4]">G</span>
        Continue with Google
      </button>

      <div className="my-7 flex items-center gap-4">
        <div className="h-px flex-1 bg-cyan-400/15" />
        <span className="text-[10px] font-medium tracking-wider text-slate-600">
          OR
        </span>
        <div className="h-px flex-1 bg-cyan-400/15" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-2 block text-[12px] font-semibold tracking-wider text-[#8793aa]">
            Email
          </span>

          <input
            value={emailAddress}
            onChange={(event) => setEmailAddress(event.target.value)}
            type="email"
            placeholder="you@chatterlite.dev"
            autoComplete="email"
            required
            className="h-11 w-full rounded-xl border border-cyan-400/25 bg-[#02091c] px-4 text-sm text-[#eafaff] outline-none transition placeholder:text-[#46546c] focus:border-cyan-300 focus:ring-1 focus:ring-cyan-300/25"
          />
        </label>

        <label className="block">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[12px] font-semibold tracking-wider text-[#8793aa]">
              Password
            </span>

            <Link
              href="/forgot-password"
              className="text-[12px] font-extrabold text-[#52e6f7] hover:text-[#a2f5ff]"
            >
              Forgot?
            </Link>
          </div>

          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            required
            className="h-11 w-full rounded-xl border border-cyan-400/25 bg-[#02091c] px-4 text-sm text-[#eafaff] outline-none transition placeholder:text-[#46546c] focus:border-cyan-300 focus:ring-1 focus:ring-cyan-300/25"
          />
        </label>

        {errorMessage ? (
          <p className="rounded-xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {errorMessage}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={isLoading}
          className="mt-5 h-12 w-full rounded-xl bg-[#43ddf4] text-[15px] font-extrabold text-[#020617] shadow-[0_0_34px_rgba(67,221,244,0.45)] transition hover:bg-[#67eaff] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isLoading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-center text-[13px] font-semibold text-slate-500">
        New to ChatterLite?{" "}
        <Link
          href="/sign-up"
          className="font-extrabold text-[#5ee7f7] hover:text-[#a2f5ff]"
        >
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}