import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Card, CardContent, CardHeader, CardTitle, 
  Badge, Button, ScrollArea, Input, 
  Alert, AlertTitle, AlertDescription, Separator 
} from "@/components/ui";
import { 
  Send, RotateCcw, Building2, User, 
  Bot, AlertCircle, TrendingUp, Users, 
  ShieldAlert, Lightbulb, Target, Briefcase,
  Sparkles, ChevronRight, Activity, Globe
} from "lucide-react";
import { researchCompany, generateSessionId } from "@/lib/api";
import type { ChatMessage, AccountPlan, DiffResult } from "@/lib/types";
import { cn } from "@/lib/utils";

function App() {
  const [sessionId] = useState(() => generateSessionId());
  const [userMessage, setUserMessage] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [plan, setPlan] = useState<AccountPlan | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResult>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const handleSend = async () => {
    if (!userMessage.trim() || isLoading) return;

    const currentMsg = userMessage;
    setUserMessage("");
    setError(null);
    setIsLoading(true);

    const newUserMessage: ChatMessage = { role: "user", content: currentMsg };
    const updatedHistory = [...chatHistory, newUserMessage];
    setChatHistory(updatedHistory);

    try {
      const result = await researchCompany({
        user_message: currentMsg,
        company_name: companyName,
        session_id: sessionId,
        chat_history: chatHistory,
        current_plan: plan,
      });

      setChatHistory(result.chat_history);
      setPlan(result.plan);
      setDiffResult(result.diff_result);
      setCompanyName(result.company_name);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
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
    setError(null);
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
      default: return <Building2 className="w-5 h-5" />;
    }
  };

  const getSectionColor = (key: string) => {
    switch (key) {
      case "opportunities": return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
      case "risks": return "text-rose-400 bg-rose-400/10 border-rose-400/20";
      case "recommended_actions": return "text-amber-400 bg-amber-400/10 border-amber-400/20";
      default: return "text-primary bg-primary/10 border-primary/20";
    }
  };

  const renderSection = (title: string, content: string, sectionKey: string) => {
    const isList = [
      "competitors", 
      "opportunities", 
      "risks", 
      "recommended_actions", 
      "products_services"
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
          "group h-full rounded-3xl border border-white/5 bg-white/[0.03] backdrop-blur-md p-6 transition-all hover:bg-white/[0.05] hover:border-white/10",
          sectionKey === "overview" ? "md:col-span-2" : ""
        )}
      >
        <div className="flex items-center gap-4 mb-6">
          <div className={cn("p-3 rounded-2xl", colors)}>
            {getSectionIcon(sectionKey)}
          </div>
          <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-white/50 group-hover:text-white/80 transition-colors">
            {title.replace(/_/g, " ")}
          </h3>
        </div>
        <div className="space-y-4">
          {isList ? (
            <ul className="space-y-3">
              {content.split("\n").filter(line => line.trim()).map((line, i) => (
                <li key={i} className="flex items-start gap-3 text-sm leading-relaxed text-white/70">
                  <div className={cn("mt-1.5 w-1.5 h-1.5 rounded-full shrink-0", colors.split(" ")[0])} />
                  <span>{line.replace(/^[•\-\*]\s*/, "")}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm leading-relaxed text-white/70 whitespace-pre-wrap">{content}</p>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-[#0A0A0B] text-white selection:bg-primary/30 overflow-hidden font-outfit">
      {/* Header */}
      <header className="flex items-center justify-between px-10 py-6 border-b border-white/5 bg-black/40 backdrop-blur-2xl sticky top-0 z-50">
        <div className="flex items-center gap-6">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative p-3 bg-black rounded-2xl leading-none flex items-center border border-white/10">
              <Sparkles className="w-6 h-6 text-primary" />
            </div>
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/50">
              STRATOS <span className="text-primary/80">AI</span>
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-[0.4em] text-white/30">Strategic Intelligence System</p>
          </div>
          <AnimatePresence>
            {companyName && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <Badge className="ml-4 px-4 py-1.5 rounded-full bg-primary/10 text-primary border-primary/20 font-bold hover:bg-primary/20 transition-all cursor-default">
                  <Globe className="w-3 h-3 mr-2" />
                  {companyName}
                </Badge>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={resetState} className="rounded-full px-6 text-white/40 hover:text-white hover:bg-white/5 transition-all font-bold tracking-widest text-[10px] uppercase">
            <RotateCcw className="w-3.5 h-3.5 mr-2" />
            Wipe System
          </Button>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden">
        {/* Left Column: Intelligence Hub (Chat) */}
        <section className="w-full lg:w-[40%] flex flex-col border-r border-white/5 bg-white/[0.01]">
          <ScrollArea className="flex-1 p-10" ref={scrollRef}>
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
                      <div className="relative p-8 bg-black/40 border border-white/10 rounded-[2.5rem] shadow-2xl backdrop-blur-xl">
                        <Activity className="w-12 h-12 text-primary" />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <h2 className="text-3xl font-black tracking-tighter">System Ready</h2>
                      <p className="text-white/40 max-w-xs mx-auto text-sm leading-relaxed font-medium italic">
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
                      "p-3 rounded-2xl shadow-xl border transition-all", 
                      msg.role === "user" 
                        ? "bg-primary border-white/20 text-white" 
                        : "bg-black/40 border-white/10 text-primary"
                    )}>
                      {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div className={cn(
                      "max-w-[85%] rounded-[2rem] px-6 py-5 text-sm leading-relaxed shadow-2xl border backdrop-blur-sm",
                      msg.role === "user" 
                        ? "bg-primary/20 border-primary/30 rounded-tr-none text-white font-medium" 
                        : "bg-white/[0.03] border-white/5 rounded-tl-none text-white/80"
                    )}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {isLoading && (
                <motion.div 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }}
                  className="flex items-start gap-4"
                >
                  <div className="p-3 rounded-2xl bg-black/40 border border-white/10 text-primary">
                    <Bot className="w-4 h-4 animate-pulse" />
                  </div>
                  <div className="bg-white/[0.03] border border-white/5 rounded-[2rem] rounded-tl-none px-6 py-5 flex gap-2 items-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" />
                  </div>
                </motion.div>
              )}
            </div>
          </ScrollArea>

          <div className="p-10 bg-black/60 backdrop-blur-3xl border-t border-white/5">
            <div className="max-w-xl mx-auto relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-purple-600/50 rounded-[1.5rem] blur opacity-0 group-focus-within:opacity-30 transition duration-500"></div>
              <Input
                placeholder="Target corporation or strategic query..."
                className="relative pr-16 py-8 rounded-[1.5rem] border-white/10 bg-white/[0.03] focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all font-semibold text-base placeholder:text-white/20 text-white shadow-2xl"
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
                <Send className="w-5 h-5 text-white" />
              </Button>
            </div>
          </div>
        </section>

        {/* Right Column: Strategic Canvas */}
        <section className="hidden lg:flex flex-1 flex-col bg-black/20">
          <ScrollArea className="flex-1 px-14 py-12">
            <div className="max-w-6xl mx-auto space-y-12">
              {!plan ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center justify-center min-h-[75vh] text-center border-2 border-dashed border-white/5 rounded-[3rem] bg-white/[0.01] p-16 space-y-8"
                >
                  <div className="relative group">
                    <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full group-hover:bg-primary/40 transition-all duration-1000" />
                    <div className="relative p-12 bg-black border border-white/5 rounded-[3rem] shadow-2xl">
                      <Target className="w-24 h-24 text-white/10 group-hover:text-primary/30 transition-all duration-500" />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-black tracking-tight text-white/40">Canvas Locked</h3>
                    <p className="text-white/20 max-w-sm mx-auto leading-relaxed text-sm font-medium">
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
                      className="bg-primary/5 border border-primary/20 rounded-[2.5rem] p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden"
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
                            className="bg-black/40 rounded-2xl border border-white/5 p-5 relative group overflow-hidden"
                          >
                            <div className="font-black text-white/30 mb-4 uppercase tracking-tighter text-[10px] flex items-center justify-between">
                              {section.replace(/_/g, " ")}
                              <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </div>
                            <div className="space-y-2">
                              <div className="p-4 text-white/30 bg-white/[0.02] rounded-xl border border-white/5 text-xs line-through italic">
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
                  <div className="flex items-end justify-between gap-8 border-b border-white/5 pb-10">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <Badge className="bg-primary/10 text-primary border-primary/20 font-black text-[10px] tracking-widest uppercase py-1 px-3">Live Feed</Badge>
                        <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.4em]">Strategic Assessment</span>
                      </div>
                      <h2 className="text-6xl font-black tracking-tighter text-white">
                        {companyName}
                      </h2>
                    </div>
                    <div className="flex flex-col items-end gap-2 text-right">
                       <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.4em]">Verification ID</p>
                       <p className="text-xs font-mono text-white/40">{sessionId.split('-')[0]}</p>
                    </div>
                  </div>

                  {/* Bento Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderSection("Executive Overview", plan.overview, "overview")}
                    {Object.entries(plan)
                      .filter(([key]) => key !== "overview" && key !== "company_name")
                      .map(([key, value]) => renderSection(key, value, key))
                    }
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </section>
      </main>
    </div>
  );
}

export default App;

