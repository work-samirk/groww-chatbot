"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const chatCanvasRef = useRef(null);
  const textareaRef = useRef(null);

  // Suggestions for the welcome state
  const suggestions = [
    "What is the exit load of Groww Nifty 50 Index Fund?",
    "Who is the fund manager for Groww Flexi Cap Fund?",
    "What is the minimum SIP amount?",
    "What is the expense ratio of Groww Large Cap Fund?",
    "How to start a SIP on Groww?",
  ];

  // Auto-scroll to bottom of chat when messages change
  useEffect(() => {
    if (chatCanvasRef.current) {
      chatCanvasRef.current.scrollTo({
        top: chatCanvasRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isThinking]);

  // Handle auto-resizing of the input textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  };

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query) return;

    // Reset input
    if (!textToSend) {
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }

    // Add user message
    const userMessageId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { id: userMessageId, sender: "user", text: query },
    ]);

    setIsThinking(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      // Format message history
      const history = messages.map(msg => ({
        sender: msg.sender,
        text: msg.text
      }));

      const response = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query, history }),
      });

      if (!response.ok) {
        throw new Error("Failed to connect to the backend server.");
      }

      const data = await response.json();
      
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "assistant",
          text: data.answer,
          source_link: data.source_link,
          last_updated: data.last_updated,
          is_refusal: data.is_refusal,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "assistant",
          text: "Sorry, I am unable to connect to the backend service. Please check if the backend server is running.",
          is_refusal: true,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Helper to parse simple markdown to react elements (bold text)
  const formatText = (text) => {
    if (!text) return "";
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={index} className="font-semibold text-on-surface">{part.slice(2, -2)}</strong>;
      }
      // Handle newlines
      const subparts = part.split("\n");
      return subparts.map((sub, idx) => (
        <span key={`${index}-${idx}`}>
          {sub}
          {idx < subparts.length - 1 && <br />}
        </span>
      ));
    });
  };

  const startNewDiscussion = () => {
    setMessages([]);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background text-on-background font-body-md selection:bg-primary-container selection:text-on-primary-container">
      {/* Side Navigation (Desktop Only) */}
      <aside className={`flex flex-col h-full p-stack-md bg-surface-container border-r border-outline-variant w-64 transition-all duration-300 md:flex ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0 md:w-0 overflow-hidden md:p-0 md:border-r-0"}`}>
        <div className="mb-stack-lg flex items-center justify-center entrance-anim">
          <img
            alt="Groww Logo"
            className="h-10 w-auto object-contain"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDpl7Gk8AvLkwLk8rmKYPyRyCeIf3_foLlJ-8DZuEnNDePrSiNYqQk_kY55Vu5sJJlze4Z7WULGEz52K2Ee5pr29-6tumhNPmAaWACsVtxUnjVvM0x6QNkT5xeXuqGfopKWLi8cYISd-WWaM8D4fMPJX-IA8gGn3AcWuIr3DhtdpJw_-lp1EXQ0y84WPSAOntoPlq6dl2u79wBLPJGH02wJ768amEP-ssRZUNPCiysC0s0cuNenAQhk28Fl3nK9FnzhqTxFrYMQoto"
          />
        </div>
        <button
          onClick={startNewDiscussion}
          className="mb-stack-lg flex items-center justify-center gap-stack-sm bg-primary-container text-on-primary-container py-3 px-4 rounded-xl font-label-lg transition-transform active:scale-95 hover:opacity-90 shadow-sm entrance-anim delay-1"
        >
          <span className="material-symbols-outlined">add</span>
          <span>New Discussion</span>
        </button>
        <nav className="flex flex-col gap-stack-xs flex-1 entrance-anim delay-2">
          <button className="flex items-center gap-stack-sm p-3 bg-primary-container text-on-primary-container rounded-lg font-label-lg transition-all w-full text-left">
            <span className="material-symbols-outlined">chat</span>
            <span>Chat</span>
          </button>
          <button className="flex items-center gap-stack-sm p-3 text-on-surface-variant hover:bg-surface-variant rounded-lg font-label-lg transition-all w-full text-left">
            <span className="material-symbols-outlined">history</span>
            <span>History</span>
          </button>
          <button className="flex items-center gap-stack-sm p-3 text-on-surface-variant hover:bg-surface-variant rounded-lg font-label-lg transition-all w-full text-left">
            <span className="material-symbols-outlined">account_balance_wallet</span>
            <span>Saved Funds</span>
          </button>
          <button className="flex items-center gap-stack-sm p-3 text-on-surface-variant hover:bg-surface-variant rounded-lg font-label-lg transition-all mt-auto w-full text-left">
            <span className="material-symbols-outlined">settings</span>
            <span>Settings</span>
          </button>
        </nav>
        <div className="mt-stack-lg p-stack-sm flex items-center gap-stack-sm border-t border-outline-variant pt-stack-md entrance-anim delay-3">
          <img
            alt="User Profile"
            className="w-8 h-8 rounded-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAGai3GvZWgDo9dh85Ap6A7xJ6Q4W4j62eL-yUA_7O2lK1f1H84T8ypHKshv0-h2L7y526EkoGC8wYCrCP4gCPejBP6YHjLQfrk329wFoQjZre4QlZp62SW4l8IdKZc1cvsNNHowJ6sX1j03qyVqaeJ9RdVgHgWkAHsT9oStBwDgSqx8iiUgnclNEinh3zYSwRNPFD-Ht1zMep0sgncYp54Cp97cl4R2EOzSYVfjorKbol3kKZTYPSU2s8xMqrcS2ka7u2wDgEjKz8"
          />
          <div className="flex flex-col">
            <span className="font-label-lg text-label-lg text-on-surface">Investor Account</span>
            <span className="font-label-md text-label-md text-on-surface-variant">Verified Portfolio</span>
          </div>
        </div>
      </aside>

      {/* Main Content Canvas */}
      <main className="flex-1 flex flex-col min-w-0 bg-surface relative chat-bg-gradient">
        {/* Top App Bar */}
        <header className="flex justify-between items-center w-full px-container-margin py-stack-md sticky top-0 z-50 bg-surface/80 backdrop-blur-sm border-b border-outline-variant/10">
          <div className="flex items-center entrance-anim ml-4 gap-2">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-full hover:bg-surface-variant transition-colors active:scale-95 md:flex hidden"
            >
              <span className="material-symbols-outlined text-on-surface-variant">menu</span>
            </button>
            <img
              alt="Groww Logo"
              className="h-8 w-auto object-contain"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDpl7Gk8AvLkwLk8rmKYPyRyCeIf3_foLlJ-8DZuEnNDePrSiNYqQk_kY55Vu5sJJlze4Z7WULGEz52K2Ee5pr29-6tumhNPmAaWACsVtxUnjVvM0x6QNkT5xeXuqGfopKWLi8cYISd-WWaM8D4fMPJX-IA8gGn3AcWuIr3DhtdpJw_-lp1EXQ0y84WPSAOntoPlq6dl2u79wBLPJGH02wJ768amEP-ssRZUNPCiysC0s0cuNenAQhk28Fl3nK9FnzhqTxFrYMQoto"
            />
          </div>
          <div className="flex items-center gap-stack-sm entrance-anim mr-4">
            <button className="p-2 rounded-full hover:bg-surface-variant transition-colors active:scale-95 duration-150">
              <span className="material-symbols-outlined text-on-surface-variant">info</span>
            </button>
            <button className="p-2 rounded-full hover:bg-surface-variant transition-colors active:scale-95 duration-150">
              <span className="material-symbols-outlined text-on-surface-variant">history</span>
            </button>
          </div>
        </header>

        {/* Disclaimer Banner */}
        <div className="mx-auto w-full max-w-4xl px-container-margin mt-stack-sm entrance-anim delay-1">
          <div className="bg-error-container/30 border border-error/10 text-on-tertiary-container px-4 py-2 rounded-lg flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">warning</span>
            <span className="font-label-md text-label-md">Facts-only. No investment advice.</span>
          </div>
        </div>

        {/* Chat Area */}
        <section
          ref={chatCanvasRef}
          className="flex-1 overflow-y-auto hide-scrollbar px-container-margin py-stack-lg flex flex-col gap-stack-lg items-center pb-32"
          id="chat-canvas"
        >
          <div className="w-full max-w-3xl flex flex-col gap-stack-lg">
            {messages.length === 0 && !isThinking ? (
              /* Empty State Welcome */
              <div className="flex flex-col items-center py-section-padding entrance-anim delay-2">
                <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-stack-md text-primary">
                  <span className="material-symbols-outlined text-[32px]">auto_awesome</span>
                </div>
                <h1 className="font-headline-lg text-headline-lg text-on-surface mb-stack-sm text-center">
                  How can I help you with Groww Funds?
                </h1>
                <p className="font-body-lg text-body-lg text-on-surface-variant max-w-md mb-stack-lg text-center">
                  Ask any factual question about SIPs, exit loads, fund managers, or specific Groww mutual fund details.
                </p>
                <div className="w-full max-w-2xl mt-8">
                  <div className="flex items-center gap-2 mb-6 px-4">
                    <span className="material-symbols-outlined text-primary text-[20px]">auto_awesome</span>
                    <h2 className="font-label-lg text-on-surface">A few ideas to get you started</h2>
                  </div>
                  {/* Staggered Suggestions Pills */}
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap gap-2 justify-start">
                      {suggestions.slice(0, 2).map((item, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(item)}
                          className="px-5 py-2.5 bg-surface-container-low border border-primary/20 hover:border-primary/50 hover:bg-white text-primary rounded-full font-label-md text-label-md transition-all shadow-sm active:scale-95 text-left"
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2 justify-start md:ml-8">
                      {suggestions.slice(2, 3).map((item, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(item)}
                          className="px-5 py-2.5 bg-surface-container-low border border-tertiary/20 hover:border-tertiary/50 hover:bg-white text-tertiary rounded-full font-label-md text-label-md transition-all shadow-sm active:scale-95 text-left"
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2 justify-start">
                      {suggestions.slice(3).map((item, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(item)}
                          className="px-5 py-2.5 bg-surface-container-low border border-on-surface-variant/20 hover:border-on-surface-variant/50 hover:bg-white text-on-surface-variant rounded-full font-label-md text-label-md transition-all shadow-sm active:scale-95 text-left"
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              /* Chat Threads */
              <div className="flex flex-col gap-stack-lg pb-stack-lg">
                {messages.map((msg) => (
                  <div key={msg.id} className="w-full">
                    {msg.sender === "user" ? (
                      /* User Message */
                      <div className="flex justify-end entrance-anim">
                        <div className="max-w-[80%] bg-primary-container text-on-primary-container px-4 py-3 rounded-xl rounded-tr-none shadow-sm font-body-md">
                          {msg.text}
                        </div>
                      </div>
                    ) : (
                      /* Assistant Message */
                      <div className="flex justify-start gap-stack-sm entrance-anim delay-1 mt-2">
                        <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
                          <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                        </div>
                        <div className="flex flex-col gap-stack-xs max-w-[85%]">
                          <div className="bg-surface-container-low border border-outline-variant/30 px-4 py-3 rounded-xl rounded-tl-none font-body-md text-on-surface">
                            {formatText(msg.text)}
                          </div>
                          {(msg.last_updated || msg.source_link) && (
                            <div className="flex items-center gap-stack-md px-stack-sm">
                              {msg.last_updated && (
                                <span className="font-label-md text-label-md text-on-surface-variant opacity-60">
                                  Last updated from sources: {msg.last_updated}
                                </span>
                              )}
                              {msg.source_link && (
                                <a
                                  className="text-primary font-label-md text-label-md hover:underline flex items-center gap-1"
                                  href={msg.source_link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  Source <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Assistant Thinking / Loader */}
                {isThinking && (
                  <div className="flex justify-start gap-stack-sm entrance-anim delay-1 mt-2">
                    <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
                      <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                    </div>
                    <div className="flex flex-col gap-stack-xs max-w-[85%]">
                      <div className="bg-surface-container-low border border-outline-variant/30 px-4 py-3 rounded-xl rounded-tl-none font-body-md text-on-surface-variant/70 min-w-[200px]">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-100" />
                          <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-200" />
                          <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-300" />
                          <span className="text-sm font-label-md italic ml-1">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Input Bar */}
        <footer className="w-full fixed bottom-0 left-0 md:absolute md:bottom-0 bg-surface/80 backdrop-blur-md border-t border-outline-variant/20 p-stack-md md:p-stack-lg z-20">
          <div className="max-w-4xl mx-auto flex gap-stack-sm items-end">
            <div className="flex-grow glitter-border-container shadow-lg rounded-full">
              <div className="relative bg-surface-container-lowest rounded-full overflow-hidden flex items-center px-4 py-2">
                <span className="material-symbols-outlined text-on-surface-variant/60 text-xl mr-2">search</span>
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  className="w-full resize-none bg-transparent border-none px-2 py-2 font-body-md text-on-surface focus:outline-none focus:ring-0 pr-14 hide-scrollbar max-h-[150px] leading-tight"
                  placeholder="Ask a factual question about Groww mutual funds..."
                  rows="1"
                />
                <button
                  onClick={() => handleSend()}
                  className="absolute right-2 p-2 bg-primary text-on-primary rounded-full hover:opacity-90 active:scale-95 transition-all shadow-md flex items-center justify-center h-10 w-10"
                >
                  <span className="material-symbols-outlined">send</span>
                </button>
              </div>
            </div>
          </div>
          <div className="max-w-4xl mx-auto mt-stack-sm flex justify-center hidden md:flex">
            <p className="font-label-md text-label-md text-on-surface-variant opacity-50">
              Information provided is based on public fund documentation.
            </p>
          </div>
        </footer>
      </main>

      {/* Bottom Navigation (Mobile Only) */}
      <nav className="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 py-2 bg-surface shadow-md md:hidden border-t border-outline-variant/20">
        <button className="flex flex-col items-center justify-center bg-secondary-container text-on-secondary-container rounded-xl p-stack-sm active:scale-90 duration-100">
          <span className="material-symbols-outlined">chat_bubble</span>
          <span className="font-label-md text-label-md">Chat</span>
        </button>
        <button className="flex flex-col items-center justify-center text-on-surface-variant p-stack-sm hover:bg-surface-container-high active:scale-90 duration-100">
          <span className="material-symbols-outlined">search</span>
          <span className="font-label-md text-label-md">Search</span>
        </button>
        <button className="flex flex-col items-center justify-center text-on-surface-variant p-stack-sm hover:bg-surface-container-high active:scale-90 duration-100">
          <span className="material-symbols-outlined">person</span>
          <span className="font-label-md text-label-md">Profile</span>
        </button>
      </nav>
    </div>
  );
}
