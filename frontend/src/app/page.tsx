"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Card, CardContent, CardHeader, CardTitle, 
  Badge, Button, ScrollArea, Input, 
  Alert, AlertTitle, AlertDescription, Separator 
} from "@/components/ui";
import { 
  Send, RotateCcw, Building2, User, 
  Bot, AlertCircle, TrendingUp, Users, 
  ShieldAlert, Lightbulb, Target, Briefcase 
} from "lucide-react";
import { researchCompany, generateSessionId } from "@/lib/api";
import { ChatMessage, AccountPlan, DiffResult } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function CompanyResearchPage() {
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
      case "overview": return <Building2 className="w-5 h-5 text-primary" />;
      case "products_services": return <Briefcase className="w-5 h-5 text-primary" />;
      case "market_position": return <TrendingUp className="w-5 h-5 text-primary" />;
      case "competitors": return <Users className="w-5 h-5 text-primary" />;
      case "key_contacts": return <Users className="w-5 h-5 text-primary" />;
      case "opportunities": return <Lightbulb className="w-5 h-5 text-primary" />;
      case "risks": return <ShieldAlert className="w-5 h-5 text-primary" />;
      case "recommended_actions": return <Target className="w-5 h-5 text-primary" />;
      default: return <Building2 className="w-5 h-5 text-primary" />;
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

    return (
      <Card key={sectionKey} className="h-full border-primary/10 bg-card/50 backdrop-blur-sm transition-all hover:border-primary/30">
        <CardHeader className="pb-3 flex flex-row items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            {getSectionIcon(sectionKey)}
          </div>
          <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground pt-1">
            {title.replace(/_/g, " ")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isList ? (
            <ul className="list-disc pl-5 space-y-2 text-sm leading-relaxed text-foreground/80">
              {content.split("\n").filter(line => line.trim()).map((line, i) => (
                <li key={i}>{line.replace(/^[•\-\*]\s*/, "")}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm leading-relaxed text-foreground/80 whitespace-pre-wrap">{content}</p>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-background selection:bg-primary/20">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-border/50 bg-card/30 backdrop-blur-xl sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <div className="p-2.5 bg-primary/20 rounded-xl shadow-inner">
            <TrendingUp className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/60">
            Company Intelligence Agent
          </h1>
          {companyName && (
            <Badge className="ml-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary border-primary/20 font-bold transition-all animate-in fade-in zoom-in duration-300">
              {companyName}
            </Badge>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={resetState} className="rounded-full px-5 py-2 border-border/50 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 transition-all font-semibold">
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset Workspace
        </Button>
      </header>

      <main className="flex flex-1 overflow-hidden">
        {/* Left Column: Chat */}
        <section className="w-full lg:w-[42%] flex flex-col border-r border-border/50 bg-muted/20">
          <ScrollArea className="flex-1 p-8" ref={scrollRef}>
            <div className="max-w-2xl mx-auto space-y-8 pb-4">
              {chatHistory.length === 0 && (
                <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
                  <div className="relative">
                    <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
                    <div className="relative p-6 bg-card border border-primary/10 rounded-2xl shadow-xl">
                      <Bot className="w-16 h-16 text-primary opacity-40" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-2xl font-bold">Awaiting Strategy</p>
                    <p className="text-muted-foreground max-w-sm px-4">
                      Enter a company name below to begin deep-dive research into products, financials, and competitors.
                    </p>
                  </div>
                </div>
              )}
              {chatHistory.map((msg, i) => (
                <div key={i} className={cn("flex items-start gap-5", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                  <div className={cn("p-2.5 rounded-xl shrink-0 shadow-lg", msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border border-border/50")}>
                    {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-primary" />}
                  </div>
                  <div className={cn(
                    "max-w-[85%] rounded-3xl px-5 py-4 text-sm leading-relaxed shadow-sm transition-all",
                    msg.role === "user" ? "bg-primary text-primary-foreground rounded-tr-none" : "bg-card border border-border/50 rounded-tl-none text-foreground/90"
                  )}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-start gap-4 animate-pulse">
                  <div className="p-2.5 rounded-xl bg-card border border-border/40">
                    <Bot className="w-4 h-4 text-primary/40" />
                  </div>
                  <div className="bg-card/50 border border-border/40 rounded-3xl rounded-tl-none px-5 py-4">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 rounded-full bg-primary/30 animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-primary/30 animate-bounce [animation-delay:0.2s]" />
                      <div className="w-2 h-2 rounded-full bg-primary/30 animate-bounce [animation-delay:0.4s]" />
                    </div>
                  </div>
                </div>
              )}
              {error && (
                <Alert variant="destructive" className="border-destructive/20 bg-destructive/5 text-destructive rounded-2xl">
                  <AlertCircle className="w-4 h-4" />
                  <AlertTitle className="font-bold">System Alert</AlertTitle>
                  <AlertDescription className="text-sm opacity-90">{error}</AlertDescription>
                </Alert>
              )}
            </div>
          </ScrollArea>

          <div className="p-8 bg-card/60 backdrop-blur-xl border-t border-border/50">
            <div className="max-w-2xl mx-auto relative group">
              <Input
                placeholder="Ask about a company (e.g. 'Generate a brief for Groq')..."
                className="pr-14 py-8 rounded-2xl border-border bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all font-medium text-lg placeholder:text-muted-foreground/60 shadow-lg group-hover:border-primary/30"
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                disabled={isLoading}
              />
              <Button 
                size="icon" 
                onClick={handleSend} 
                disabled={!userMessage.trim() || isLoading}
                className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl h-12 w-12 bg-primary hover:bg-primary/90 transition-all shadow-xl active:scale-90"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </section>

        {/* Right Column: Structured Plan */}
        <section className="hidden lg:flex flex-1 flex-col bg-background/50">
          <ScrollArea className="flex-1 px-12 py-10">
            <div className="max-w-5xl mx-auto space-y-10">
              {!plan ? (
                <div className="flex flex-col items-center justify-center min-h-[70vh] text-center border-2 border-dashed border-border/50 rounded-[2.5rem] bg-muted/5 p-12 space-y-6">
                  <div className="p-8 bg-primary/5 rounded-full ring-1 ring-primary/10">
                    <Building2 className="w-20 h-20 text-primary/20" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-2xl font-bold">Research Portal</h3>
                    <p className="text-muted-foreground max-w-md mx-auto leading-relaxed">
                      Structured intelligence reports including market analysis, competitor landscapes, and strategic recommendations will populate here.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-10 pb-16 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                  {Object.keys(diffResult).length > 0 && (
                    <Alert className="bg-primary/5 border-primary/20 rounded-2xl px-6 py-5 shadow-sm">
                      <AlertCircle className="w-5 h-5 text-primary" />
                      <AlertTitle className="text-primary font-black uppercase text-xs tracking-widest pl-2 mb-4">
                        Delta Report: Incremental Updates Detected
                      </AlertTitle>
                      <AlertDescription>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                          {Object.entries(diffResult).map(([section, diff]) => (
                            <li key={section} className="text-xs p-4 bg-card rounded-xl border border-primary/10 shadow-sm relative overflow-hidden group">
                                <div className="absolute top-0 right-0 p-1 px-2 bg-primary/5 text-primary/40 font-black text-[10px]">CHANGED</div>
                              <div className="font-extrabold text-foreground mb-3 uppercase tracking-tighter">
                                {section.replace(/_/g, " ")}
                              </div>
                              <div className="space-y-2">
                                <div className="p-3 line-through text-destructive/50 bg-destructive/5 rounded-lg border border-destructive/10">
                                  {diff.old || "Empty State"}
                                </div>
                                <div className="p-3 text-primary bg-primary/5 rounded-lg border border-primary/20 font-bold">
                                  {diff.new}
                                </div>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="flex items-center gap-6">
                    <div className="space-y-1">
                      <h2 className="text-4xl font-black tracking-tighter text-foreground">
                        {companyName}
                      </h2>
                      <p className="text-sm font-medium text-muted-foreground uppercase tracking-[0.2em]">Strategy Intelligence Report</p>
                    </div>
                    <Separator className="flex-1 opacity-20" />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
                    <div className="md:col-span-2">
                      {renderSection("Executive Overview", plan.overview, "overview")}
                    </div>
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
