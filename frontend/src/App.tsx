import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Badge, Button, ScrollArea, Input, 
} from "@/components/ui";
import { 
  Send, RotateCcw, Building2, User, 
  Bot, TrendingUp, Users, 
  ShieldAlert, Lightbulb, Target, Briefcase,
  Sparkles, ChevronRight, Activity, Globe,
  AlertCircle, History, MessageSquare, LayoutGrid, Sun, Moon, MapPin
} from "lucide-react";
import { researchCompanyStream, generateSessionId } from "@/lib/api";
import type { ChatMessage, AccountPlan, DiffResult } from "@/lib/types";
import { cn } from "@/lib/utils";

// New Components
import { useToast } from "@/hooks/useToast";
import { ToastContainer } from "@/components/ToastContainer";
import { ExportButton } from "@/components/ExportButton";
import { HistoryPanel } from "@/components/HistoryPanel";
import { PlanSkeleton } from "@/components/PlanSkeleton";

function App() {
  const [sessionId] = useState(() => generateSessionId());
  const [userMessage, setUserMessage] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [plan, setPlan] = useState<AccountPlan | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResult>({});
  const [isLoading, setIsLoading] = useState(false);
  const [streamingReply, setStreamingReply] = useState("");
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [activeMobileTab, setActiveMobileTab] = useState<"chat" | "plan">("chat");
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    return document.documentElement.classList.contains("dark") ? "dark" : "light";
  });
  
  const { toasts, addToast, removeToast } = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, streamingReply]);

  useEffect(() => {
    if (plan && window.innerWidth < 1024) {
      setActiveMobileTab("plan");
    }
  }, [plan]);

  const handleSend = async () => {
    if (!userMessage.trim() || isLoading) return;

    const currentMsg = userMessage;
    setUserMessage("");
    setIsLoading(true);
    setStreamingReply("");

    const newUserMessage: ChatMessage = { role: "user", content: currentMsg };
    const updatedHistory = [...chatHistory, newUserMessage];
    setChatHistory(updatedHistory);

    try {
      await researchCompanyStream(
        {
          user_message: currentMsg,
          company_name: companyName,
          session_id: sessionId,
          chat_history: chatHistory,
          current_plan: plan,
        },
        (token) => {
          setStreamingReply((prev) => prev + token);
        },
        (result) => {
          // Finished streaming
          setChatHistory(result.chat_history);
          setPlan(result.plan);
          setDiffResult(result.diff_result);
          
          if (!companyName && result.company_name) {
             addToast({ type: "success", message: `Intel gathered on ${result.company_name}` });
          }
          setCompanyName(result.company_name);
          setStreamingReply("");

          // Update session storage for timeline
          const storageKey = `history_${sessionId}`;
          const currentHistoryStr = sessionStorage.getItem(storageKey);
          let sessHistory = [];
          if (currentHistoryStr) {
             try { sessHistory = JSON.parse(currentHistoryStr); } catch(e){}
          }
          sessHistory.unshift({
             company_name: result.company_name,
             researched_at: new Date().toISOString(),
             overview: result.plan.overview || "Updated profile"
          });
          sessionStorage.setItem(storageKey, JSON.stringify(sessHistory));
        },
        (errMsg) => {
          if (errMsg.includes("Invalid input detected")) {
             addToast({ type: "info", message: "Invalid input detected." });
          } else {
             addToast({ type: "error", message: errMsg });
          }
        }
      );
    } catch (err: any) {
      addToast({ type: "error", message: err.message || "An unexpected error occurred" });
    } finally {
      setIsLoading(false);
    }
  };

  const resetState = () => {
    setChatHistory([]);
    setPlan(null);
    setDiffResult({});
    setCompanyName("");
    setUserMessage("");
    setStreamingReply("");
  };

  const getSectionIcon = (key: string) => {
    switch (key) {
      case "overview": return <Building2 className="w-5 h-5" />;
      case "products_services": return <Briefcase className="w-5 h-5" />;
      case "market_position": return <TrendingUp className="w-5 h-5" />;
      case "competitors": return <Users className="w-5 h-5" />;
      case "key_contacts": return <Users className="w-5 h-5" />;
      case "opportunities": return <Lightbulb className="w-5 h-5" />;
      case "risks": return <ShieldAlert className="w-5 h-5" />;
      case "recommended_actions": return <Target className="w-5 h-5" />;
      case "locations": return <MapPin className="w-5 h-5" />;
      default: return <Building2 className="w-5 h-5" />;
    }
  };

  const getSectionColor = (key: string) => {
    switch (key) {
      case "opportunities": return "text-emerald-500 dark:text-emerald-400 bg-emerald-500/10 dark:bg-emerald-400/10 border-emerald-500/20 dark:border-emerald-400/20";
      case "risks": return "text-rose-500 dark:text-rose-400 bg-rose-500/10 dark:bg-rose-400/10 border-rose-500/20 dark:border-rose-400/20";
      case "recommended_actions": return "text-amber-500 dark:text-amber-400 bg-amber-500/10 dark:bg-amber-400/10 border-amber-500/20 dark:border-amber-400/20";
      case "locations": return "text-blue-500 dark:text-blue-400 bg-blue-500/10 dark:bg-blue-400/10 border-blue-500/20 dark:border-blue-400/20";
      default: return "text-primary bg-primary/10 border-primary/20";
    }
  };

  const renderSection = (title: string, content: string, sectionKey: string) => {
    if (!content) return null;
    
    const isList = [
      "competitors", 
      "opportunities", 
      "risks", 
      "recommended_actions", 
      "products_services",
      "locations"
    ].includes(sectionKey);

    const colors = getSectionColor(sectionKey);

    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        key={sectionKey}
        className={cn(
          "group h-full rounded-3xl border border-slate-200 dark:border-white/5 bg-slate-200/50 dark:bg-white/[0.03] backdrop-blur-md p-6 transition-all hover:bg-slate-200 dark:hover:bg-white/[0.05] hover:border-slate-300 dark:hover:border-white/10",
          sectionKey === "overview" ? "md:col-span-2" : ""
        )}
      >
        <div className="flex items-center gap-4 mb-6">
          <div className={cn("p-3 rounded-2xl", colors)}>
            {getSectionIcon(sectionKey)}
          </div>
          <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-white/50 group-hover:text-slate-700 dark:group-hover:text-white/80 transition-colors">
            {title.replace(/_/g, " ")}
          </h3>
        </div>
        <div className="space-y-4">
          {isList ? (
            <ul className="space-y-3">
              {content.split("\n").filter(line => line.trim()).map((line, i) => (
                <li key={i} className="flex items-start gap-3 text-sm leading-relaxed text-slate-700 dark:text-white/70">
                  <div className={cn("mt-1.5 w-1.5 h-1.5 rounded-full shrink-0", colors.split(" ")[0])} />
                  <span>{line.replace(/^[•\-\*]\s*/, "")}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm leading-relaxed text-slate-500 dark:text-white/70 whitespace-pre-wrap">{content}</p>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-[#0A0A0B] text-slate-900 dark:text-slate-900 dark:text-white selection:bg-primary/30 overflow-hidden font-outfit transition-colors duration-300">
      {/* Header */}
      <header className="flex items-center justify-between px-10 py-6 border-b border-slate-200 dark:border-white/5 bg-white/80 dark:bg-black/40 backdrop-blur-2xl sticky top-0 z-50">
        <div className="flex items-center gap-6">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-blue-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative p-2 bg-white dark:bg-black rounded-2xl leading-none flex items-center border border-slate-200 dark:border-white/10">
              <img src="/logo.png" alt="Company Insight AI" className="w-8 h-8 object-contain rounded-lg" />
            </div>
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-500 dark:from-white dark:to-white/50">
              COMPANY INSIGHT <span className="text-primary/80">AI</span>
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-[0.4em] text-slate-500 dark:text-white/30">Strategic Intelligence System</p>
          </div>
          <AnimatePresence>
            {companyName && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <Badge className="ml-4 px-4 py-1.5 rounded-full bg-primary/10 text-primary border-primary/20 font-bold hover:bg-primary/20 transition-all cursor-default hidden md:inline-flex">
                  <Globe className="w-3 h-3 mr-2" />
                  {companyName}
                </Badge>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => {
            const newTheme = theme === "dark" ? "light" : "dark";
            setTheme(newTheme);
            if (newTheme === "dark") {
              document.documentElement.classList.add("dark");
            } else {
              document.documentElement.classList.remove("dark");
            }
          }} className="rounded-full px-4 text-slate-500 hover:text-slate-900 dark:text-white/40 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-all">
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="sm" onClick={resetState} className="rounded-full px-6 text-slate-500 hover:text-slate-900 dark:text-white/40 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-all font-bold tracking-widest text-[10px] uppercase hidden sm:flex">
            <RotateCcw className="w-3.5 h-3.5 mr-2" />
            Wipe System
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setIsHistoryOpen(true)} className="rounded-full px-6 text-slate-500 hover:text-slate-900 dark:text-white/40 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-all font-bold tracking-widest text-[10px] uppercase">
            <History className="w-3.5 h-3.5 mr-2" />
            Timeline
          </Button>
        </div>
      </header>

      {/* Mobile Tab Bar */}
      <div className="lg:hidden flex border-b border-slate-200 dark:border-white/5 bg-white/80 dark:bg-black/40">
        <button 
          onClick={() => setActiveMobileTab("chat")}
          className={cn(
            "flex-1 py-4 text-xs font-black uppercase tracking-widest transition-colors",
            activeMobileTab === "chat" 
              ? "text-primary border-b-2 border-primary bg-primary/5" 
              : "text-white/30 hover:text-white/50"
          )}
        >
          <MessageSquare className="w-4 h-4 mx-auto mb-1" />
          Intel Hub
        </button>
        <button 
          onClick={() => setActiveMobileTab("plan")}
          className={cn(
            "flex-1 py-4 text-xs font-black uppercase tracking-widest transition-colors",
            activeMobileTab === "plan" 
              ? "text-primary border-b-2 border-primary bg-primary/5" 
              : "text-white/30 hover:text-white/50"
          )}
        >
          <LayoutGrid className="w-4 h-4 mx-auto mb-1" />
          Canvas
          {plan && activeMobileTab !== "plan" && (
            <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-primary animate-pulse relative -top-1" />
          )}
        </button>
      </div>

      <main className="flex flex-1 overflow-hidden relative">
        {/* Left Column: Intelligence Hub (Chat) */}
        <section className={cn(
          "w-full lg:w-[40%] flex-col border-r border-white/5 bg-white/[0.01]",
          activeMobileTab === "chat" ? "flex" : "hidden lg:flex"
        )}>
          <ScrollArea className="flex-1 p-4 lg:p-10" ref={scrollRef}>
            <div className="max-w-xl mx-auto space-y-10 pb-4">
              <AnimatePresence mode="popLayout">
                {chatHistory.length === 0 && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-8"
                  >
                    <div className="relative animate-float">
                      <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
                      <div className="relative p-6 bg-white dark:bg-black border border-slate-200 dark:border-white/10 rounded-[2.5rem] shadow-2xl backdrop-blur-xl flex items-center justify-center">
                        <img src="/logo.png" alt="Company Insight AI" className="w-16 h-16 object-contain rounded-xl" />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <h2 className="text-3xl font-black tracking-tighter">System Ready</h2>
                      <p className="text-slate-500 dark:text-white/40 max-w-xs mx-auto text-sm leading-relaxed font-medium italic">
                        "Initiate a strategic scan by entering a corporate entity below."
                      </p>
                    </div>
                  </motion.div>
                )}
                {chatHistory.map((msg, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className={cn("flex items-start gap-4", msg.role === "user" ? "flex-row-reverse" : "flex-row")}
                  >
                    <div className={cn(
                      "p-3 rounded-2xl shadow-xl border transition-all shrink-0", 
                      msg.role === "user" 
                        ? "bg-primary border-primary/50 text-white" 
                        : "bg-white/80 dark:bg-black/40 border-slate-200 dark:border-white/10 text-primary"
                    )}>
                      {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div className={cn(
                      "max-w-[85%] rounded-[2rem] px-6 py-5 text-sm leading-relaxed shadow-2xl border backdrop-blur-sm",
                      msg.role === "user" 
                        ? "bg-primary/20 border-primary/30 rounded-tr-none text-slate-900 dark:text-white font-medium" 
                        : "bg-slate-200/50 dark:bg-white/[0.03] border-slate-200 dark:border-white/5 rounded-tl-none text-slate-700 dark:text-white/80"
                    )}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </motion.div>
                ))}
                
                {/* Streaming Reply Bubble */}
                {isLoading && streamingReply && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className="flex items-start gap-4 flex-row"
                  >
                    <div className="p-3 rounded-2xl shadow-xl border transition-all shrink-0 bg-white/80 dark:bg-black/40 border-slate-200 dark:border-white/10 text-primary">
                      <Bot className="w-4 h-4 animate-pulse" />
                    </div>
                    <div className="max-w-[85%] rounded-[2rem] px-6 py-5 text-sm leading-relaxed shadow-2xl border backdrop-blur-sm bg-slate-200/50 dark:bg-white/[0.03] border-slate-200 dark:border-white/5 rounded-tl-none text-slate-700 dark:text-white/80">
                      <p className="whitespace-pre-wrap">
                        {streamingReply}
                        <span className="animate-pulse font-bold text-primary ml-1">▋</span>
                      </p>
                    </div>
                  </motion.div>
                )}
                
                {/* Initial Loading Spinner (before streaming starts) */}
                {isLoading && !streamingReply && (
                  <motion.div 
                    initial={{ opacity: 0 }} 
                    animate={{ opacity: 1 }}
                    className="flex items-start gap-4"
                  >
                    <div className="p-3 rounded-2xl bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 text-primary shrink-0">
                      <Bot className="w-4 h-4 animate-pulse" />
                    </div>
                    <div className="bg-white/[0.03] border border-slate-200 dark:border-white/5 rounded-[2rem] rounded-tl-none px-6 py-5 flex gap-2 items-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </ScrollArea>

          <div className="p-4 lg:p-10 bg-white/80 dark:bg-black/60 backdrop-blur-3xl border-t border-slate-200 dark:border-white/5">
            <div className="max-w-xl mx-auto relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-purple-600/50 rounded-[1.5rem] blur opacity-0 group-focus-within:opacity-30 transition duration-500"></div>
              <Input
                placeholder="Target corporation or strategic query..."
                className="relative pr-16 py-8 rounded-[1.5rem] border-slate-200 dark:border-white/10 bg-white/[0.03] focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all font-semibold text-base placeholder:text-slate-500 dark:text-white/20 text-slate-900 dark:text-white shadow-2xl"
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                disabled={isLoading}
              />
              <Button 
                size="icon" 
                onClick={handleSend} 
                disabled={!userMessage.trim() || isLoading}
                className="absolute right-3 top-1/2 -translate-y-1/2 rounded-2xl h-12 w-12 bg-primary hover:bg-primary/90 transition-all shadow-xl active:scale-95 glow-primary"
              >
                <Send className="w-5 h-5 text-slate-900 dark:text-white" />
              </Button>
            </div>
          </div>
        </section>

        {/* Right Column: Strategic Canvas */}
        <section className={cn(
          "flex-1 flex-col bg-white dark:bg-black/20",
          activeMobileTab === "plan" ? "flex" : "hidden lg:flex"
        )}>
          <ScrollArea className="flex-1 px-4 py-8 lg:px-14 lg:py-12">
            <div className="max-w-6xl mx-auto space-y-12">
              {isLoading && !plan ? (
                <PlanSkeleton />
              ) : !plan ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center justify-center min-h-[75vh] text-center border-2 border-dashed border-slate-200 dark:border-white/5 rounded-[3rem] bg-white/[0.01] p-8 lg:p-16 space-y-8"
                >
                  <div className="relative group">
                    <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full group-hover:bg-primary/40 transition-all duration-1000" />
                    <div className="relative p-12 bg-white dark:bg-black border border-slate-200 dark:border-white/5 rounded-[3rem] shadow-2xl">
                      <Target className="w-24 h-24 text-slate-500 dark:text-white/10 group-hover:text-primary/30 transition-all duration-500" />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-black tracking-tight text-slate-500 dark:text-white/40">Canvas Locked</h3>
                    <p className="text-slate-500 dark:text-white/20 max-w-sm mx-auto leading-relaxed text-sm font-medium">
                      Establish a target entity to unlock deep-dive market intelligence and strategic forecasts.
                    </p>
                  </div>
                </motion.div>
              ) : (
                <div className="space-y-12 pb-24">
                  {/* Delta Alert */}
                  {Object.keys(diffResult).length > 0 && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-primary/5 border border-primary/20 rounded-[2.5rem] p-6 lg:p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 p-3 px-6 bg-primary/20 text-primary font-black text-[10px] uppercase tracking-widest rounded-bl-3xl">Delta Stream Active</div>
                      <div className="flex items-center gap-3 mb-8">
                        <Activity className="w-5 h-5 text-primary" />
                        <h4 className="text-primary font-black uppercase text-xs tracking-[0.3em]">Incremental Intelligence Update</h4>
                      </div>
                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        {Object.entries(diffResult).map(([section, diff]) => (
                          <motion.div 
                            layout
                            key={section} 
                            className="bg-white/80 dark:bg-black/40 rounded-2xl border border-slate-200 dark:border-white/5 p-5 relative group overflow-hidden"
                          >
                            <div className="font-black text-slate-500 dark:text-white/30 mb-4 uppercase tracking-tighter text-[10px] flex items-center justify-between">
                              {section.replace(/_/g, " ")}
                              <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </div>
                            <div className="space-y-2">
                              <div className="p-4 text-slate-500 dark:text-white/30 bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-xs line-through italic">
                                {diff.old || "Empty State"}
                              </div>
                              <div className="p-4 text-primary bg-primary/10 rounded-xl border border-primary/20 text-sm font-bold shadow-inner">
                                {diff.new}
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {/* Plan Header */}
                  <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 border-b border-slate-200 dark:border-white/5 pb-10">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <Badge className="bg-primary/10 text-primary border-primary/20 font-black text-[10px] tracking-widest uppercase py-1 px-3">Live Feed</Badge>
                        <span className="text-[10px] font-black text-slate-500 dark:text-white/20 uppercase tracking-[0.4em]">Strategic Assessment</span>
                      </div>
                      <div className="flex items-center gap-4 flex-wrap">
                        <h2 className="text-4xl lg:text-6xl font-black tracking-tighter text-slate-900 dark:text-white">
                          {companyName}
                        </h2>
                        <ExportButton plan={plan} companyName={companyName} />
                      </div>
                    </div>
                    <div className="flex flex-row md:flex-col items-center md:items-end gap-4 md:gap-2 text-right">
                       <p className="text-[10px] font-black text-slate-500 dark:text-white/20 uppercase tracking-[0.4em]">Verification ID</p>
                       <p className="text-xs font-mono text-slate-500 dark:text-white/40">{sessionId.split('-')[0]}</p>
                    </div>
                  </div>

                  {/* Media Gallery */}
                  {plan.company_images && plan.company_images.length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {plan.company_images.slice(0, 4).map((img, idx) => (
                        <div key={idx} className="relative aspect-video rounded-2xl overflow-hidden border border-slate-200 dark:border-white/10 group bg-slate-100 dark:bg-white/[0.02]">
                          <img src={img} alt={`${companyName} reference`} className="object-cover w-full h-full opacity-90 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700" />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Bento Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderSection("Executive Overview", plan.overview, "overview")}
                    {Object.entries(plan)
                      .filter(([key]) => key !== "overview" && key !== "company_name" && key !== "company_images" && key !== "session_id" && key !== "id" && key !== "researched_at")
                      .map(([key, value]) => renderSection(key, value as string, key))
                    }
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </section>

        <AnimatePresence>
          {isHistoryOpen && (
            <HistoryPanel 
              companyName={companyName} 
              sessionId={sessionId} 
              onClose={() => setIsHistoryOpen(false)} 
            />
          )}
        </AnimatePresence>
      </main>

      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
}

export default App;
