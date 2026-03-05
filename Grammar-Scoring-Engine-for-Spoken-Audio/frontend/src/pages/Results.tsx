import { Link, Navigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Download, RefreshCw, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

type PredictResponse = {
  success: boolean;
  filename: string;
  duration: number;
  transcript: string;
  score: number;
  predicted_class: number;
  confidence: number;
  processing_time: number;
};

const getPerformanceLabel = (score: number) => {
  if (score < 2) return "Poor";
  if (score < 3.5) return "Average";
  if (score < 4.5) return "Good";
  return "Excellent";
};

const ScoreCircle = ({ score, maxScore }: { score: number; maxScore: number }) => {
  const percentage = (score / maxScore) * 100;
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-44 h-44 mx-auto">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/20" />
        <defs>
          <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(185 100% 50%)" />
            <stop offset="100%" stopColor="hsl(265 90% 60%)" />
          </linearGradient>
        </defs>
        <motion.circle
          cx="50" cy="50" r="45" fill="none" strokeWidth="8" strokeLinecap="round"
          stroke="url(#scoreGrad)"
          initial={{ strokeDasharray: circumference, strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut", delay: 0.3 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="text-4xl font-bold text-foreground">
          {score.toFixed(2)}
        </motion.span>
      </div>
    </div>
  );
};

const ResultsPage = () => {
  const location = useLocation();
  const analysis = (location.state as { analysis?: PredictResponse } | null)?.analysis;

  console.log("ResultsPage - Full location:", location);
  console.log("ResultsPage - Location state:", location.state);
  console.log("ResultsPage - Analysis data:", analysis);

  if (!analysis) {
    console.warn("No analysis data found, redirecting to upload");
    return <Navigate to="/upload" replace />;
  }

  const performanceLabel = getPerformanceLabel(analysis.score);

  const getLabelColor = (label: string) => {
    switch (label.toLowerCase()) {
      case "poor": return "bg-destructive/20 text-destructive";
      case "average": return "bg-warning/20 text-warning";
      case "good": return "bg-primary/20 text-primary";
      case "excellent": return "bg-success/20 text-success";
      default: return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="relative pt-24 lg:pt-28 pb-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold">
                <span className="text-foreground">Analysis </span>
                <span className="gradient-text">Results</span>
              </h1>
              <p className="text-muted-foreground mt-1">
                {analysis.filename} • {analysis.duration.toFixed(2)}s • processed in {analysis.processing_time.toFixed(2)}s
              </p>
            </div>
            <Button className="bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:opacity-90 rounded-full px-6">
              <Download className="w-4 h-4 mr-2" />
              Download Report
            </Button>
          </motion.div>

          {/* Score Card - full width */}
          <div className="mb-8">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="rounded-2xl border border-border/40 bg-card/50 p-8 max-w-sm mx-auto">
              <h3 className="text-lg font-semibold text-foreground mb-6 text-center">Overall Grammar Score</h3>
              <ScoreCircle score={analysis.score} maxScore={5} />
              <div className="text-center mt-5">
                <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium ${getLabelColor(performanceLabel)}`}>
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {performanceLabel}
                </span>
                <p className="text-sm text-muted-foreground mt-2">Out of 5.0</p>
              </div>
            </motion.div>
          </div>

          {/* Full Transcript */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="rounded-2xl border border-border/40 bg-card/50 p-8">
            <h3 className="text-lg font-semibold text-foreground mb-4">Transcript</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{analysis.transcript}</p>
          </motion.div>

          {/* Actions */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="flex justify-center gap-4 mt-10">
            <Link to="/upload">
              <Button variant="outline" className="rounded-full border-border/60 px-6">
                <RefreshCw className="w-4 h-4 mr-2" />
                Analyze Another
              </Button>
            </Link>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default ResultsPage;
