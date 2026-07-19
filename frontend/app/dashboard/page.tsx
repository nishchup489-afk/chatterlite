"use client";

import { FormEvent, useMemo, useState } from "react";

type ChatMessage = {
  id: string;
  senderId: string;
  content: string;
  createdAt: string;
  type: "text" | "system";
};

type Chat = {
  id: string;
  name: string;
  username: string;
  avatarFallback: string;
  isOnline: boolean;
  lastMessage: string;
  lastMessageAt: string;
  unreadCount: number;
  messages: ChatMessage[];
};

const CURRENT_USER_ID = "me";

const initialChats: Chat[] = [
  {
    id: "chat_1",
    name: "Sadman",
    username: "@sadman",
    avatarFallback: "S",
    isOnline: true,
    lastMessage: "Bro the WebSocket is finally alive 🔥",
    lastMessageAt: "10:42 AM",
    unreadCount: 2,
    messages: [
      {
        id: "msg_1",
        senderId: "system",
        content: "Conversation started.",
        createdAt: "10:20 AM",
        type: "system",
      },
      {
        id: "msg_2",
        senderId: "chat_1",
        content: "Yo, did you finish the message model?",
        createdAt: "10:38 AM",
        type: "text",
      },
      {
        id: "msg_3",
        senderId: CURRENT_USER_ID,
        content: "Almost. I fixed the User and Message relationships.",
        createdAt: "10:40 AM",
        type: "text",
      },
      {
        id: "msg_4",
        senderId: "chat_1",
        content: "Bro the WebSocket is finally alive 🔥",
        createdAt: "10:42 AM",
        type: "text",
      },
    ],
  },
  {
    id: "chat_2",
    name: "ChatterLite Room",
    username: "#general",
    avatarFallback: "C",
    isOnline: true,
    lastMessage: "Redis pub/sub next?",
    lastMessageAt: "9:15 AM",
    unreadCount: 0,
    messages: [
      {
        id: "msg_5",
        senderId: "chat_2",
        content: "Redis pub/sub next?",
        createdAt: "9:15 AM",
        type: "text",
      },
    ],
  },
  {
    id: "chat_3",
    name: "AI Agent",
    username: "@agent",
    avatarFallback: "AI",
    isOnline: false,
    lastMessage: "I can help summarize this room later.",
    lastMessageAt: "Yesterday",
    unreadCount: 0,
    messages: [
      {
        id: "msg_6",
        senderId: "chat_3",
        content: "I can help summarize this room later.",
        createdAt: "Yesterday",
        type: "text",
      },
    ],
  },
];

function createMessageId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `msg_${Date.now()}`;
}

export default function MessagesPage() {
  const [chats, setChats] = useState<Chat[]>(initialChats);
  const [activeChatId, setActiveChatId] = useState(initialChats[0]?.id ?? "");
  const [draftMessage, setDraftMessage] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredChats = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    if (!query) return chats;

    return chats.filter((chat) => {
      return (
        chat.name.toLowerCase().includes(query) ||
        chat.username.toLowerCase().includes(query)
      );
    });
  }, [chats, searchQuery]);

  const activeChat = chats.find((chat) => chat.id === activeChatId);

  function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanMessage = draftMessage.trim();

    if (!cleanMessage || !activeChat) return;

    const now = new Date();

    const newMessage: ChatMessage = {
      id: createMessageId(),
      senderId: CURRENT_USER_ID,
      content: cleanMessage,
      createdAt: now.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
      }),
      type: "text",
    };

    setChats((currentChats) =>
      currentChats.map((chat) => {
        if (chat.id !== activeChat.id) return chat;

        return {
          ...chat,
          lastMessage: cleanMessage,
          lastMessageAt: newMessage.createdAt,
          unreadCount: 0,
          messages: [...chat.messages, newMessage],
        };
      })
    );

    setDraftMessage("");
  }

  function handleSelectChat(chatId: string) {
    setActiveChatId(chatId);

    setChats((currentChats) =>
      currentChats.map((chat) => {
        if (chat.id !== chatId) return chat;

        return {
          ...chat,
          unreadCount: 0,
        };
      })
    );
  }

  return (
    <main className="min-h-screen bg-[#050816] text-white">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-4 md:px-6">
        <div className="mb-4 flex items-center justify-between rounded-3xl border border-white/10 bg-white/3 px-5 py-4 shadow-2xl shadow-cyan-500/5">
          <div>
            <p className="text-sm text-cyan-300">ChatterLite</p>
            <h1 className="text-2xl font-bold tracking-tight">
              Messages Dashboard
            </h1>
          </div>

          <div className="hidden rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-200 md:block">
            WebSocket ready
          </div>
        </div>

        <div className="grid flex-1 gap-4 overflow-hidden md:grid-cols-[360px_1fr]">
          <aside className="flex min-h-80 flex-col overflow-hidden rounded-3xl border border-white/10 bg-white/4">
            <div className="border-b border-white/10 p-4">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">Chats</h2>
                  <p className="text-sm text-white/50">
                    One-to-one, rooms, and agents
                  </p>
                </div>

                <button className="rounded-full bg-cyan-400 px-4 py-2 text-sm font-semibold text-black transition hover:bg-cyan-300">
                  New
                </button>
              </div>

              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search chats..."
                className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-cyan-400/60"
              />
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {filteredChats.map((chat) => {
                const isActive = chat.id === activeChatId;

                return (
                  <button
                    key={chat.id}
                    onClick={() => handleSelectChat(chat.id)}
                    className={`mb-2 flex w-full items-center gap-3 rounded-2xl p-3 text-left transition ${
                      isActive
                        ? "bg-cyan-400 text-black"
                        : "bg-transparent hover:bg-white/6"
                    }`}
                  >
                    <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-black/40 font-bold">
                      {chat.avatarFallback}

                      <span
                        className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 ${
                          isActive ? "border-cyan-400" : "border-[#111827]"
                        } ${
                          chat.isOnline ? "bg-emerald-400" : "bg-zinc-500"
                        }`}
                      />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <h3 className="truncate font-semibold">{chat.name}</h3>
                        <span
                          className={`shrink-0 text-xs ${
                            isActive ? "text-black/70" : "text-white/40"
                          }`}
                        >
                          {chat.lastMessageAt}
                        </span>
                      </div>

                      <div className="mt-1 flex items-center justify-between gap-2">
                        <p
                          className={`truncate text-sm ${
                            isActive ? "text-black/70" : "text-white/45"
                          }`}
                        >
                          {chat.lastMessage}
                        </p>

                        {chat.unreadCount > 0 && (
                          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-300 px-1.5 text-xs font-bold text-black">
                            {chat.unreadCount}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </aside>

          <section className="flex min-h-150 flex-col overflow-hidden rounded-3xl border border-white/10 bg-white/4">
            {activeChat ? (
              <>
                <header className="flex items-center justify-between border-b border-white/10 p-4">
                  <div className="flex items-center gap-3">
                    <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400 font-bold text-black">
                      {activeChat.avatarFallback}

                      <span
                        className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-[#101827] ${
                          activeChat.isOnline ? "bg-emerald-400" : "bg-zinc-500"
                        }`}
                      />
                    </div>

                    <div>
                      <h2 className="font-semibold">{activeChat.name}</h2>
                      <p className="text-sm text-white/45">
                        {activeChat.isOnline ? "Online now" : "Offline"} ·{" "}
                        {activeChat.username}
                      </p>
                    </div>
                  </div>

                  <button className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/70 transition hover:border-cyan-400/40 hover:text-cyan-200">
                    Details
                  </button>
                </header>

                <div className="flex-1 space-y-4 overflow-y-auto p-4">
                  {activeChat.messages.map((message) => {
                    const isMine = message.senderId === CURRENT_USER_ID;

                    if (message.type === "system") {
                      return (
                        <div key={message.id} className="flex justify-center">
                          <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-white/40">
                            {message.content}
                          </span>
                        </div>
                      );
                    }

                    return (
                      <div
                        key={message.id}
                        className={`flex ${isMine ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[82%] rounded-3xl px-4 py-3 text-sm leading-relaxed md:max-w-[62%] ${
                            isMine
                              ? "rounded-br-md bg-cyan-400 text-black"
                              : "rounded-bl-md bg-white/10 text-white"
                          }`}
                        >
                          <p>{message.content}</p>

                          <p
                            className={`mt-2 text-right text-[11px] ${
                              isMine ? "text-black/55" : "text-white/35"
                            }`}
                          >
                            {message.createdAt}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <form
                  onSubmit={handleSendMessage}
                  className="border-t border-white/10 p-4"
                >
                  <div className="flex items-end gap-3 rounded-3xl border border-white/10 bg-black/30 p-2">
                    <textarea
                      value={draftMessage}
                      onChange={(event) => setDraftMessage(event.target.value)}
                      placeholder="Write a message..."
                      rows={1}
                      className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-white/35"
                      onKeyDown={(event) => {
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          event.currentTarget.form?.requestSubmit();
                        }
                      }}
                    />

                    <button
                      type="submit"
                      disabled={!draftMessage.trim()}
                      className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-bold text-black transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      Send
                    </button>
                  </div>

                  <p className="mt-2 text-xs text-white/35">
                    Press Enter to send. Shift + Enter for a new line.
                  </p>
                </form>
              </>
            ) : (
              <div className="flex flex-1 items-center justify-center p-6 text-center">
                <div>
                  <h2 className="text-xl font-semibold">No chat selected</h2>
                  <p className="mt-2 text-white/45">
                    Pick a chat from the sidebar to start messaging.
                  </p>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}