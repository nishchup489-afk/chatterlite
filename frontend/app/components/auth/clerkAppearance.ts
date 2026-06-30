export const chatterLiteClerkAppearance = {
  variables: {
    colorPrimary: "#43ddf4",
    colorBackground: "transparent",
    colorText: "#e5faff",
    colorTextSecondary: "#8390a6",
    colorInputBackground: "#03091c",
    colorInputText: "#e5faff",
    colorDanger: "#fb7185",
    borderRadius: "0.75rem",
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
  },

  elements: {
    rootBox: "w-full",
    cardBox: "w-full bg-transparent shadow-none",
    card: "w-full border-0 bg-transparent p-0 shadow-none",

    header: "items-start text-left",
    headerTitle:
      "text-[28px] font-extrabold leading-[1.05] tracking-[-0.04em] text-[#e5faff]",
    headerSubtitle: "mt-3 text-[15px] leading-6 text-[#8490a6]",

    socialButtons: "mt-7",
    socialButtonsBlockButton:
      "h-11 rounded-[11px] border border-cyan-400/25 bg-[#02091c] text-[#e5faff] shadow-none transition hover:border-cyan-300/40 hover:bg-[#06162c]",
    socialButtonsBlockButtonText: "text-[14px] font-bold",
    socialButtonsProviderIcon: "text-[#47dff4]",

    dividerRow: "my-7",
    dividerLine: "bg-cyan-400/15",
    dividerText:
      "px-4 text-[10px] font-medium uppercase tracking-[0.24em] text-slate-600",

    form: "space-y-4",
    formField: "space-y-2",
    formFieldLabel:
      "text-[12px] font-semibold tracking-[0.05em] text-[#8793aa]",
    formFieldInput:
      "h-11 rounded-[11px] border border-cyan-400/25 bg-[#02091c] px-4 text-[14px] text-[#e5faff] shadow-none outline-none transition placeholder:text-[#46546c] focus:border-cyan-300 focus:ring-1 focus:ring-cyan-300/25",
    formFieldAction:
      "text-[12px] font-extrabold text-[#52e6f7] hover:text-[#a2f5ff]",

    formButtonPrimary:
      "mt-5 h-12 rounded-[12px] bg-[#43ddf4] text-[15px] font-extrabold text-[#020617] shadow-[0_0_34px_rgba(67,221,244,0.45)] transition hover:bg-[#67eaff]",

    footer: "bg-transparent",
    footerAction: "mt-6 text-center",
    footerActionText: "text-[13px] font-semibold text-slate-500",
    footerActionLink:
      "text-[13px] font-extrabold text-[#5ee7f7] hover:text-[#a2f5ff]",

    alert: "rounded-xl border border-rose-400/20 bg-rose-500/10 text-rose-100",
    formFieldErrorText: "text-[12px] text-rose-300",
  },
};

export const chatterLiteLocalization = {
  signIn: {
    start: {
      title: "Welcome back",
      subtitle: "Sign in to reconnect to your rooms and threads.",
      actionText: "New to ChatterLite?",
      actionLink: "Create one",
    },
  },
  signUp: {
    start: {
      title: "Create account",
      subtitle: "Create your ChatterLite account and start building rooms.",
      actionText: "Already have an account?",
      actionLink: "Sign in",
    },
  },
  formFieldLabel__emailAddress: "Email",
  formFieldInputPlaceholder__emailAddress: "you@chatterlite.dev",
  formFieldLabel__password: "Password",
  formFieldAction__forgotPassword: "Forgot?",
};