"use client";

import { useEffect, useRef, useState } from "react";

type ChatMessage = {
  id: number;
  name: string;
  text: string;
  side: "in" | "out";
};

type PreviewEvent =
  | {
      type: "typing";
      name: string;
    }
  | {
      type: "in" | "out";
      name: string;
      text: string;
    };

const previewScript: PreviewEvent[] = [
  { type: "typing", name: "maya" },
  { type: "in", name: "maya", text: "wait the latency is unreal 👀" },
  { type: "typing", name: "nish" },
  { type: "out", name: "nish", text: "told you — built socket-up" },
];

const featureCards = [
  {
    icon: "✉",
    title: "Private Messages",
    text: "Send live one-to-one messages between authenticated users with instant delivery.",
  },
  {
    icon: "#",
    title: "Room Conversations",
    text: "Create shared spaces where multiple users talk in real time, no refresh needed.",
  },
  {
    icon: "◉",
    title: "Presence Engine",
    text: "Track who is online, typing, disconnected, or reconnecting at a glance.",
  },
  {
    icon: "⟲",
    title: "Message History",
    text: "Conversations are persisted so users return without losing any context.",
  },
  {
    icon: "⚡",
    title: "Production WebSocket Core",
    text: "Auth, connection cleanup, and scalable architecture baked in from day one.",
  },
];

const steps = [
  {
    number: "1",
    title: "User signs in",
    text: "Clerk authenticates the user and provides a real, verified identity.",
  },
  {
    number: "2",
    title: "Socket connects",
    text: "The frontend opens a WebSocket using the authenticated user ID.",
  },
  {
    number: "3",
    title: "Server routes messages",
    text: "FastAPI tracks active connections and delivers to the right user or room.",
  },
  {
    number: "4",
    title: "Database stores history",
    text: "Messages persist so conversations survive refreshes and reconnects.",
  },
];

const stackItems = [
  ["frontend", "Next.js"],
  ["ui", "React"],
  ["styles", "Tailwind"],
  ["auth", "Clerk"],
  ["backend", "FastAPI"],
  ["realtime", "WebSocket"],
  ["db", "PostgreSQL"],
  ["orm", "SQLAlchemy"],
  ["pubsub", "Redis"],
];

const roadmapItems = [
  {
    label: "BUILT",
    marker: "✓",
    labelClass: "text-emerald-300",
    cardClass: "bg-cyan-400/[0.04]",
    items: ["Basic WebSocket connection", "One-to-one message prototype"],
  },
  {
    label: "IN PROGRESS",
    marker: "▸",
    labelClass: "text-cyan-300",
    cardClass: "bg-slate-900/40",
    items: ["Clerk authentication", "Message UI", "Conversation state"],
  },
  {
    label: "COMING SOON",
    marker: "○",
    labelClass: "text-slate-400",
    cardClass: "bg-slate-900/30",
    items: [
      "Room messages",
      "Active status",
      "Typing indicators",
      "Redis Pub/Sub",
      "Notifications",
      "Audio call reconnection",
    ],
  },
];

export default function LandingPage() {
  const year = new Date().getFullYear().toString();

  const eventIndexRef = useRef(0);

  const [typingName, setTypingName] = useState<string | null>("maya");

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      name: "nish",
      text: "yo you online?",
      side: "in",
    },
    {
      id: 2,
      name: "alex",
      text: "yeah, socket is live ⚡",
      side: "out",
    },
  ]);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    function playPreview() {
      const event = previewScript[eventIndexRef.current % previewScript.length];
      eventIndexRef.current += 1;

      if (event.type === "typing") {
        setTypingName(event.name);
        timeoutId = setTimeout(playPreview, 1400);
        return;
      }

      setTypingName(null);

      setMessages((currentMessages) => {
        const nextMessage: ChatMessage = {
          id: Date.now(),
          name: event.name,
          text: event.text,
          side: event.type,
        };

        return [...currentMessages, nextMessage].slice(-4);
      });

      timeoutId = setTimeout(playPreview, 2200);
    }

    timeoutId = setTimeout(playPreview, 1600);

    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="h-full w-full min-h-screen overflow-hidden bg-[#020617] text-cyan-50">
      <style jsx global>{`
        @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap");

        html {
          scroll-behavior: smooth;
        }

        body {
          font-family: "Inter", system-ui, sans-serif;
          background: #020617;
        }

        .mono {
          font-family: "JetBrains Mono", monospace;
        }

        @keyframes rise {
          from {
            opacity: 0;
            transform: translateY(8px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .reveal {
          animation: rise 0.45s ease forwards;
        }
      `}</style>

      <div
        className="bg_glow pointer-events-none fixed inset-0 z-0"
        style={{
          background:
            "radial-gradient(circle at top right, rgba(34,211,238,0.16), transparent 35%), radial-gradient(circle at top left, rgba(56,189,248,0.13), transparent 32%), radial-gradient(circle at 50% 35%, rgba(34,211,238,0.08), transparent 42%)",
        }}
      />

      <div
        className="bg_grid pointer-events-none fixed inset-0 z-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(34,211,238,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(34,211,238,0.05) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "linear-gradient(to bottom, black, transparent 90%)",
        }}
      />



      <div className="headers w-full flex justify-between items-center m-3 p-2 fixed left-0 top-0 z-50 border-b border-cyan-400/10 bg-slate-950/70 px-6 py-4 backdrop-blur-2xl">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between">
          <div className="header_name flex items-center gap-2 text-sm font-bold tracking-tight text-cyan-50">
            <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_18px_#22d3ee] text-3xl" />
            ChatterLite
          </div>

          <div className="navs flex flex-row justify-evenly items-center gap-3 mr-3 max-md:hidden md:gap-8">
            <nav>
              <a href="#features" className="text-xs text-slate-400 transition hover:text-cyan-300">
                Features
              </a>
            </nav>
            <nav>
              <a href="#how" className="text-xs text-slate-400 transition hover:text-cyan-300">
                How it works
              </a>
            </nav>
            <nav>
              <a href="#tech" className="text-xs text-slate-400 transition hover:text-cyan-300">
                Tech
              </a>
            </nav>
            <nav>
              <a href="#roadmap" className="text-xs text-slate-400 transition hover:text-cyan-300">
                Roadmap
              </a>
            </nav>
            <nav>
              <a href="/chat">
                <button className="rounded-full border border-cyan-400/30 px-4 py-2 text-xs font-medium text-cyan-100 transition hover:bg-cyan-400/10 hover:shadow-[0_0_24px_rgba(34,211,238,0.22)]">
                  Launch App
                </button>
              </a>
            </nav>
          </div>
        </div>
      </div>



      <main className="relative z-10">
        <div className="mx-auto max-w-7xl px-6 pt-36 md:pt-40">
          <div className="hero flex justify-between items-center gap-4 flex-col lg:flex-row lg:gap-16">
            <div className="hero_cta flex flex-col justify-left items-start w-[50%] max-lg:w-full">
              <div className="live_point mb-6 inline-flex rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-xs text-cyan-300 shadow-[0_0_30px_rgba(34,211,238,0.08)]">
                <ul className="list-disc list-inside">
                  <li> WebSocket core · live </li>
                </ul>
              </div>

              <div className="hero_header max-w-3xl text-4xl font-extrabold leading-[0.95] tracking-[-0.04em] text-cyan-50 md:text-6xl">
                Real-time messaging,{" "}
                <span className="cyan_text bg-linear-to-r from-cyan-200 to-sky-400 bg-clip-text text-transparent">
                  rebuilt from first principles.
                </span>
              </div>

              <div className="hero_text mt-6 max-w-xl text-base leading-7 text-slate-400 md:text-lg">
                A modern chat app powered by WebSockets, authentication, rooms,
                presence, and live message delivery. Built to understand how
                real-time systems actually work — not just how tutorials pretend
                they work.
              </div>

              <div className="buttons mt-8 flex flex-wrap gap-4">
                <a href="/chat">
                  <button className="start_chatting rounded-full bg-linear-to-r from-cyan-400 to-sky-400 px-6 py-3 text-sm font-bold text-slate-950 shadow-[0_0_35px_rgba(34,211,238,0.45)] transition hover:-translate-y-0.5 hover:shadow-[0_0_50px_rgba(34,211,238,0.65)]">
                    Start Chatting
                  </button>
                </a>

                <a href="https://github.com" target="_blank" rel="noreferrer">
                  <button className="view_github rounded-full border border-cyan-400/25 bg-cyan-400/3 px-6 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/10">
                    View GitHub →
                  </button>
                </a>
              </div>
            </div>

            <div className="hero_visual w-full lg:w-[44%]">
              <div className="chatvideo rounded-3xl border border-cyan-400/20 bg-slate-950/60 p-5 shadow-[0_30px_90px_rgba(34,211,238,0.14)] backdrop-blur-2xl">
                <div className="header flex items-center justify-between border-b border-cyan-400/10 pb-4">
                  <div className="general_and_connected">
                    <div className="general text-sm font-bold text-cyan-100"># general</div>
                    <div className="connected mt-1 text-xs text-slate-500"> 3 users connected </div>
                  </div>

                  <div className="online rounded-full bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
                    <ul className="list-disc list-inside">
                      <li>WebSocket online</li>
                    </ul>
                  </div>
                </div>

                <div className="chatwindow mt-5 flex min-h-56.25 flex-col gap-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={[
                        "reveal max-w-[82%] rounded-2xl px-4 py-3 text-sm",
                        message.side === "out"
                          ? "ml-auto bg-cyan-400/20 text-cyan-50 shadow-[0_0_25px_rgba(34,211,238,0.18)]"
                          : "mr-auto bg-slate-800/90 text-slate-200",
                      ].join(" ")}
                    >
                      <div
                        className={[
                          "mb-1 text-[11px] text-slate-500",
                          message.side === "out" ? "text-right" : "text-left",
                        ].join(" ")}
                      >
                        {message.name}
                      </div>
                      {message.text}
                    </div>
                  ))}

                  {typingName && (
                    <div className="reveal mr-auto flex max-w-[75%] items-center gap-2 rounded-2xl border border-cyan-400/10 bg-slate-950 px-4 py-3 text-sm text-slate-400">
                      {typingName} is typing
                      <span className="flex gap-1">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400 [animation-delay:150ms]" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400 [animation-delay:300ms]" />
                      </span>
                    </div>
                  )}
                </div>

                <div className="input mt-4 flex items-center gap-3 rounded-2xl border border-cyan-400/10 bg-slate-950/80 p-2">
                  <input
                    type="text"
                    placeholder="message #general"
                    disabled
                    className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-500 outline-none placeholder:text-slate-600"
                  />
                  <button className="send rounded-xl bg-cyan-400/15 px-4 py-2 text-sm font-semibold text-cyan-200">
                    ➤
                  </button>
                </div>
              </div>
            </div>
          </div>



          <hr className="my-10 border-cyan-400/10" />



          <div className="pride flex items-center gap-3 flex-wrap border-y border-cyan-400/10 py-6">
            <div className="delivery_time min-w-32">
              <div className="number mono text-xl font-bold text-cyan-100"> &lt;100ms </div>
              <div className="text text-xs text-slate-500">perceived delivery</div>
            </div>

            <div className="modes min-w-36">
              <div className="pride_feat mono text-xl font-bold text-cyan-100"> 1:1 + rooms </div>
              <div className="text text-xs text-slate-500"> messaging modes </div>
            </div>

            <div className="build_log min-w-36">
              <div className="feat mono text-xl font-bold text-cyan-100">open</div>
              <div className="text text-xs text-slate-500">source build log</div>
            </div>
          </div>



          <div id="features" className="features py-20">
            <div className="mono mb-3 text-xs uppercase tracking-[0.18em] text-cyan-400">
              // FEATURES
            </div>

            <h2 className="max-w-3xl text-3xl font-extrabold tracking-[-0.03em] text-cyan-50 md:text-4xl">
              The core of a real chat platform
            </h2>

            <div className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {featureCards.map((feature) => (
                <div
                  key={feature.title}
                  className="feature_card rounded-2xl border border-cyan-400/15 bg-cyan-400/3 p-6 transition hover:-translate-y-1 hover:border-cyan-300/40 hover:bg-cyan-400/6"
                >
                  <div className="feature_icon mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400/10 text-lg text-cyan-300">
                    {feature.icon}
                  </div>

                  <h3 className="feature_title mb-2 text-base font-bold text-cyan-50">
                    {feature.title}
                  </h3>

                  <p className="feature_text text-sm leading-6 text-slate-400">
                    {feature.text}
                  </p>
                </div>
              ))}
            </div>
          </div>



          <div id="how" className="how_it_works py-16">
            <div className="mono mb-3 text-xs uppercase tracking-[0.18em] text-cyan-400">
              // HOW IT WORKS
            </div>

            <h2 className="text-3xl font-extrabold tracking-[-0.03em] text-cyan-50 md:text-4xl">
              From sign-in to live message
            </h2>

            <div className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
              {steps.map((step) => (
                <div
                  key={step.number}
                  className="step rounded-2xl border border-cyan-400/10 bg-slate-900/40 p-5"
                >
                  <div className="step_number mono mb-4 flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-400 text-sm font-black text-slate-950">
                    {step.number}
                  </div>

                  <h3 className="step_title mb-2 text-base font-bold text-cyan-50">
                    {step.title}
                  </h3>

                  <p className="step_text text-sm leading-6 text-slate-400">
                    {step.text}
                  </p>
                </div>
              ))}
            </div>
          </div>



          <div id="tech" className="stack py-16">
            <div className="rounded-3xl border border-cyan-400/10 bg-slate-900/40 p-8 shadow-[0_0_60px_rgba(34,211,238,0.08)]">
              <div className="mono mb-3 text-xs uppercase tracking-[0.18em] text-cyan-400">
                // STACK
              </div>

              <h2 className="text-3xl font-extrabold tracking-[-0.03em] text-cyan-50 md:text-4xl">
                Built on a real production path
              </h2>

              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400 md:text-base">
                A pragmatic, scalable stack — from authenticated WebSockets today
                to Redis-powered fan-out tomorrow.
              </p>

              <div className="stack_items mt-7 flex flex-wrap gap-3">
                {stackItems.map(([label, value]) => (
                  <div
                    key={value}
                    className="stack_chip mono rounded-full border border-cyan-400/20 bg-cyan-400/4 px-4 py-2 text-xs text-cyan-100 transition hover:bg-cyan-400/10 hover:shadow-[0_0_20px_rgba(34,211,238,0.16)]"
                  >
                    <span className="text-slate-500">{label}</span>{" "}
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>



          <div id="roadmap" className="roadmap py-16">
            <div className="mono mb-3 text-xs uppercase tracking-[0.18em] text-cyan-400">
              // ROADMAP
            </div>

            <h2 className="text-3xl font-extrabold tracking-[-0.03em] text-cyan-50 md:text-4xl">
              An honest build journey
            </h2>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400 md:text-base">
              No fake &quot;everything works&quot; promises. Here&apos;s exactly
              where ChatterLite stands.
            </p>

            <div className="roadmap_grid mt-8 grid gap-5 md:grid-cols-3">
              {roadmapItems.map((column) => (
                <div
                  key={column.label}
                  className={[
                    "roadmap_column min-h-48 rounded-2xl border border-cyan-400/10 p-6",
                    column.cardClass,
                  ].join(" ")}
                >
                  <div
                    className={[
                      "roadmap_label mono mb-5 text-xs font-bold tracking-[0.18em]",
                      column.labelClass,
                    ].join(" ")}
                  >
                    {column.label}
                  </div>

                  <ul className="roadmap_list space-y-3">
                    {column.items.map((item) => (
                      <li
                        key={item}
                        className="roadmap_item flex gap-3 text-sm text-slate-300"
                      >
                        <span className={column.labelClass}>{column.marker}</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>



          <div className="launchpad my-16 rounded-3xl border border-cyan-400/20 bg-slate-900/40 px-6 py-14 text-center shadow-[0_0_70px_rgba(34,211,238,0.13)]">
            <div className="launch_hero text-3xl font-extrabold tracking-[-0.03em] text-cyan-50 md:text-4xl">
              Ready to test real-time messaging?
            </div>

            <div className="launch_hero_text mx-auto mt-4 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">
              ChatterLite is being built as a full-stack WebSocket playground —
              from auth to rooms to production-scale realtime systems.
            </div>

            <div className="launch_buttons mt-8 flex flex-wrap justify-center gap-4">
              <a href="/chat">
                <button className="cyan-button rounded-full bg-linear-to-r from-cyan-400 to-sky-400 px-7 py-3 text-sm font-bold text-slate-950 shadow-[0_0_35px_rgba(34,211,238,0.45)] transition hover:-translate-y-0.5 hover:shadow-[0_0_50px_rgba(34,211,238,0.65)]">
                  Launch App
                </button>
              </a>

              <a href="#roadmap">
                <button className="rounded-full border border-cyan-400/25 bg-cyan-400/3 px-7 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/10">
                  View Build Log →
                </button>
              </a>
            </div>
          </div>



          <footer className="flex justify-between items-center bottom-0 m-2 flex-wrap gap-5 border-t border-cyan-400/10 py-8">
            <div className="titel flex gap-3">
              <div className="title text-sm font-bold text-cyan-50">
                <ul className="list-disc list-inside">
                  <li>ChatterLite</li>
                </ul>
              </div>

              <div className="subtitle text-sm text-slate-500">
                # WebSocket playground
              </div>
            </div>

            <div className="nav flex justify-between gap-3 md:gap-6">
              <nav className="feature">
                <a href="#features" className="text-sm text-slate-400 transition hover:text-cyan-300">
                  Features
                </a>
              </nav>

              <nav className="tech">
                <a href="#tech" className="text-sm text-slate-400 transition hover:text-cyan-300">
                  Tech
                </a>
              </nav>

              <nav className="Roadmap">
                <a href="#roadmap" className="text-sm text-slate-400 transition hover:text-cyan-300">
                  Roadmap
                </a>
              </nav>

              <nav className="Github">
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-slate-400 transition hover:text-cyan-300"
                >
                  GitHub
                </a>
              </nav>
            </div>

            <div className="time mono text-xs text-slate-600">
              <p>&copy; {year} · built in public</p>
            </div>
          </footer>
        </div>
      </main>
    </div>
  );
}