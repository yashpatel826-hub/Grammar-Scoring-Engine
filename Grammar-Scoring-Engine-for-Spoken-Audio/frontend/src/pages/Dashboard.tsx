import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Clock3, FileAudio, History, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { useAuth } from "@/contexts/AuthContext";
import { getAnalysisHistory, type AnalysisRecord } from "@/lib/analysisHistory";

const formatDate = (isoDate: string) => {
  try {
    return new Date(isoDate).toLocaleString();
  } catch {
    return isoDate;
  }
};

const getPerformanceLabel = (score: number) => {
  if (score < 2) return "Poor";
  if (score < 3.5) return "Average";
  if (score < 4.5) return "Good";
  return "Excellent";
};

const getLabelColor = (label: string) => {
  switch (label.toLowerCase()) {
    case "poor":
      return "bg-destructive/20 text-destructive";
    case "average":
      return "bg-warning/20 text-warning";
    case "good":
      return "bg-primary/20 text-primary";
    case "excellent":
      return "bg-success/20 text-success";
    default:
      return "bg-muted text-muted-foreground";
  }
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [history, setHistory] = useState<AnalysisRecord[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    let active = true;

    const loadHistory = async () => {
      if (!user?.email) {
        if (active) {
          setHistory([]);
          setHistoryError(null);
        }
        return;
      }

      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const data = await getAnalysisHistory(user.email);
        if (active) {
          setHistory(data);
        }
      } catch (error) {
        if (active) {
          setHistory([]);
          setHistoryError(error instanceof Error ? error.message : "Failed to load history");
        }
      } finally {
        if (active) {
          setHistoryLoading(false);
        }
      }
    };

    loadHistory();

    return () => {
      active = false;
    };
  }, [user?.email]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="relative pt-24 lg:pt-28 pb-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4"
          >
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold">
                <span className="text-foreground">Your </span>
                <span className="gradient-text">Dashboard</span>
              </h1>
              <p className="text-muted-foreground mt-1">
                {history.length} past analysis{history.length === 1 ? "" : "es"}
              </p>
            </div>
            <Link to="/upload">
              <Button className="bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:opacity-90 rounded-full px-6">
                <Sparkles className="w-4 h-4 mr-2" />
                New Analysis
              </Button>
            </Link>
          </motion.div>

          {historyLoading ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-border/40 bg-card/50 p-10 text-center"
            >
              <h3 className="text-lg font-semibold text-foreground mb-2">Loading analysis history...</h3>
              <p className="text-sm text-muted-foreground">Please wait while we fetch your saved reports.</p>
            </motion.div>
          ) : history.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-border/40 bg-card/50 p-10 text-center"
            >
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary/15 to-secondary/20 flex items-center justify-center">
                <History className="w-7 h-7 text-primary/80" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">No analysis history yet</h3>
              <p className="text-sm text-muted-foreground mb-6">
                Analyze your first audio file to start building your personal history.
              </p>
              {historyError && (
                <p className="text-sm text-destructive mb-4">{historyError}</p>
              )}
              <Link to="/upload">
                <Button variant="outline" className="rounded-full border-border/60 px-6">
                  Analyze Audio
                </Button>
              </Link>
            </motion.div>
          ) : (
            <div className="grid gap-4">
              {history.map((item, index) => {
                const label = getPerformanceLabel(item.score);

                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.04 }}
                    className="rounded-2xl border border-border/40 bg-card/50 p-6"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                          <FileAudio className="w-4 h-4" />
                          <span className="truncate">{item.filename}</span>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {item.transcript || "No transcript available."}
                        </p>
                        <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                          <span className="inline-flex items-center gap-1">
                            <Clock3 className="w-3.5 h-3.5" />
                            {formatDate(item.createdAt)}
                          </span>
                          <span>{item.duration.toFixed(2)}s</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 lg:pl-6">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getLabelColor(label)}`}>
                          {label}
                        </span>
                        <div className="text-right min-w-[74px]">
                          <p className="text-xs text-muted-foreground">Score</p>
                          <p className="text-lg font-semibold text-foreground">{item.score.toFixed(2)}/5</p>
                        </div>
                        <Button
                          variant="outline"
                          className="rounded-full border-border/60"
                          onClick={() => navigate("/results", { state: { analysis: item } })}
                        >
                          View
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Dashboard;
