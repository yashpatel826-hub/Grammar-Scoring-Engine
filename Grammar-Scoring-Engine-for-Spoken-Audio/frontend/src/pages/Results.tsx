import { Link, Navigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Download, RefreshCw, AlertTriangle } from "lucide-react";
import { jsPDF } from "jspdf";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { type PredictResponse } from "@/lib/analysisHistory";

const getPerformanceLabel = (score: number) => {
  if (score < 2) return "Poor";
  if (score < 3.5) return "Average";
  if (score < 4.5) return "Good";
  return "Excellent";
};

type DiffKind = "same" | "removed" | "added";

type DiffToken = {
  text: string;
  kind: DiffKind;
};

const tokenizeWords = (text: string) =>
  text
    .trim()
    .split(/\s+/)
    .filter(Boolean);

const buildWordDiff = (original: string, corrected: string) => {
  const source = tokenizeWords(original);
  const target = tokenizeWords(corrected);

  const n = source.length;
  const m = target.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));

  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      if (source[i] === target[j]) {
        dp[i][j] = 1 + dp[i + 1][j + 1];
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
  }

  const leftTokens: DiffToken[] = [];
  const rightTokens: DiffToken[] = [];

  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (source[i] === target[j]) {
      leftTokens.push({ text: source[i], kind: "same" });
      rightTokens.push({ text: target[j], kind: "same" });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      leftTokens.push({ text: source[i], kind: "removed" });
      i += 1;
    } else {
      rightTokens.push({ text: target[j], kind: "added" });
      j += 1;
    }
  }

  while (i < n) {
    leftTokens.push({ text: source[i], kind: "removed" });
    i += 1;
  }

  while (j < m) {
    rightTokens.push({ text: target[j], kind: "added" });
    j += 1;
  }

  return { leftTokens, rightTokens };
};

const renderDiffTokens = (tokens: DiffToken[], side: "left" | "right") =>
  tokens.map((token, idx) => {
    const isRemoved = side === "left" && token.kind === "removed";
    const isAdded = side === "right" && token.kind === "added";

    const className = isRemoved
      ? "bg-destructive/20 text-destructive px-1 py-0.5 rounded"
      : isAdded
      ? "bg-success/20 text-success px-1 py-0.5 rounded"
      : "text-muted-foreground";

    return (
      <span key={`${side}-${idx}`} className={className}>
        {token.text}{" "}
      </span>
    );
  });

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

  if (!analysis) {
    return <Navigate to="/upload" replace />;
  }

  const performanceLabel = getPerformanceLabel(analysis.score);
  const hasCorrection =
    Boolean(analysis.corrected_text) &&
    analysis.corrected_text !== analysis.transcript;
  const diffView = buildWordDiff(analysis.transcript || "", analysis.corrected_text || "");

  const getLabelColor = (label: string) => {
    switch (label.toLowerCase()) {
      case "poor": return "bg-destructive/20 text-destructive";
      case "average": return "bg-warning/20 text-warning";
      case "good": return "bg-primary/20 text-primary";
      case "excellent": return "bg-success/20 text-success";
      default: return "bg-muted text-muted-foreground";
    }
  };

  const handleDownloadReport = () => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let cursorY = 18;

    doc.setFontSize(18);
    doc.text("Grammar Scoring Report", 14, cursorY);
    cursorY += 10;

    doc.setFontSize(11);
    doc.text(`Generated At: ${new Date().toLocaleString()}`, 14, cursorY);
    cursorY += 10;

    doc.setFontSize(13);
    doc.text("Analysis Summary", 14, cursorY);
    cursorY += 8;

    doc.setFontSize(11);
    const summaryLines = [
      `File Name: ${analysis.filename}`,
      `Duration: ${analysis.duration.toFixed(2)}s`,
      `Processing Time: ${analysis.processing_time.toFixed(2)}s`,
      `Overall Score: ${analysis.score.toFixed(2)} / 5.00`,
      `Performance Label: ${performanceLabel}`,
    ];

    summaryLines.forEach((line) => {
      doc.text(line, 14, cursorY);
      cursorY += 7;
    });

    cursorY += 3;
    doc.setFontSize(13);
    doc.text("Transcript", 14, cursorY);
    cursorY += 8;

    doc.setFontSize(11);
    const transcript = analysis.transcript || "No transcript available.";
    const wrappedTranscript = doc.splitTextToSize(transcript, pageWidth - 28);
    doc.text(wrappedTranscript, 14, cursorY);

    if (hasCorrection && analysis.corrected_text) {
      cursorY += wrappedTranscript.length * 5 + 12;
      doc.setFontSize(13);
      doc.text("Corrected Grammar", 14, cursorY);
      cursorY += 8;

      doc.setFontSize(11);
      const wrappedCorrection = doc.splitTextToSize(analysis.corrected_text, pageWidth - 28);
      doc.text(wrappedCorrection, 14, cursorY);
    }

    const sanitizedBaseName = analysis.filename.replace(/\.[^/.]+$/, "").replace(/[^a-z0-9-_]/gi, "_");
    doc.save(`${sanitizedBaseName || "analysis_report"}_report.pdf`);
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
            <Button
              onClick={handleDownloadReport}
              className="bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:opacity-90 rounded-full px-6"
            >
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

          {analysis.correction_available && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="rounded-2xl border border-border/40 bg-card/50 p-8 mt-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Grammer Correction</h3>

              {hasCorrection ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
                    <h4 className="text-sm font-semibold text-destructive mb-2">Wrong</h4>
                    <p className="text-sm leading-relaxed break-words">{renderDiffTokens(diffView.leftTokens, "left")}</p>
                  </div>

                  <div className="rounded-xl border border-success/30 bg-success/5 p-4">
                    <h4 className="text-sm font-semibold text-success mb-2">Correct</h4>
                    <p className="text-sm leading-relaxed break-words">{renderDiffTokens(diffView.rightTokens, "right")}</p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground leading-relaxed">No grammar changes were suggested for this transcript.</p>
              )}

              {analysis.correction_error && (
                <p className="text-xs text-warning mt-3">
                  Correction warning: {analysis.correction_error}
                </p>
              )}
            </motion.div>
          )}

          {/* Error Summary Section */}
          {analysis.error_summary && analysis.error_summary.total_errors > 0 && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="rounded-2xl border border-border/40 bg-card/50 p-8 mt-6">
              <div className="space-y-4">
                {/* Error Count */}
                <div className="rounded-lg border border-warning/30 bg-warning/5 p-4">
                  <p className="text-sm font-semibold text-warning">
                    {analysis.error_summary.total_errors} Grammar Issue{analysis.error_summary.total_errors !== 1 ? 's' : ''} Found
                  </p>
                </div>

                {/* Improvement Suggestions */}
                {analysis.suggestions && analysis.suggestions.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-foreground mb-3">💡 Improvement Suggestions</h4>
                    <div className="space-y-2">
                      {analysis.suggestions.map((suggestion, idx) => (
                        <div key={idx} className="flex gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
                          <div className="flex-shrink-0">
                            <div className="flex items-center justify-center h-5 w-5 rounded-full bg-primary/20 mt-0.5">
                              <span className="text-xs text-primary font-semibold">{idx + 1}</span>
                            </div>
                          </div>
                          <p className="text-sm text-muted-foreground leading-relaxed">{suggestion}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error Details */}
                {analysis.errors && analysis.errors.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-foreground mb-3">🔍 Detailed Error Analysis</h4>
                    <div className="space-y-2">
                      {analysis.errors.map((error, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-destructive/5 border border-destructive/20">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0">
                              <span className="inline-block h-5 w-5 rounded-full bg-destructive/20 flex items-center justify-center mt-0.5">
                                <span className="text-xs text-destructive font-semibold">!</span>
                              </span>
                            </div>
                            <div className="flex-grow">
                              <p className="text-sm font-medium text-foreground">
                                {error.type ? `${error.type.charAt(0).toUpperCase() + error.type.slice(1).replace(/_/g, ' ')}` : 'Grammar Error'}
                              </p>
                              {error.explanation && (
                                <p className="text-xs text-muted-foreground mt-1">{error.explanation}</p>
                              )}
                              {error.original && error.corrected && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Changed from "<span className="text-destructive font-medium">{error.original}</span>" to "
                                  <span className="text-success font-medium">{error.corrected}</span>"
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

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
