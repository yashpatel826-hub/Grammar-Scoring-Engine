import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  Cell,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Flame,
  Zap,
  BarChart3,
  Calendar,
  Clock,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

interface AnalyticsSummary {
  current_score: number;
  avg_7day: number;
  avg_30day: number;
  improvement_pct: number;
  total_sessions: number;
  total_speaking_minutes: number;
  current_streak: number;
  best_session: {
    score: number;
    date: string;
    session_id: string;
  } | null;
  peak_time: string;
}

interface ScoreTrendPoint {
  date: string;
  score: number;
}

interface ErrorBreakdown {
  articles: number;
  tense: number;
  preposition: number;
  agreement: number;
  other: number;
}

interface HeatmapData {
  day: string;
  counts: number[];
}

interface Insight {
  most_improved_area: {
    category: string;
    improvement_pct: number;
  } | null;
  most_repeated_error: {
    category: string;
    count: number;
  } | null;
  peak_time: string;
  best_session: {
    score: number;
    date: string;
  } | null;
}

interface Recommendation {
  label: string;
  message: string;
}

interface SessionData {
  id: string;
  createdAt: string;
  transcript: string;
  score: number;
  duration: number;
  error_summary: Record<string, number>;
  corrected_text: string;
}

const Dashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [scoreTrend, setScoreTrend] = useState<ScoreTrendPoint[]>([]);
  const [errorBreakdown, setErrorBreakdown] = useState<ErrorBreakdown | null>(
    null
  );
  const [heatmap, setHeatmap] = useState<HeatmapData[]>([]);
  const [insights, setInsights] = useState<Insight | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [sessionHistory, setSessionHistory] = useState<SessionData[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionData | null>(
    null
  );
  const [showReviewModal, setShowReviewModal] = useState(false);

  // Fetch all analytics data
  useEffect(() => {
    if (!user?.email) return;

    const fetchAnalytics = async () => {
      try {
        setLoading(true);

        const [summaryRes, trendRes, errorRes, heatmapRes, insightsRes, recsRes, historyRes] =
          await Promise.all([
            fetch(
              `${API_BASE_URL}/api/analytics/summary?email=${encodeURIComponent(user.email)}`
            ),
            fetch(
              `${API_BASE_URL}/api/analytics/score-trend?email=${encodeURIComponent(user.email)}&days=30`
            ),
            fetch(
              `${API_BASE_URL}/api/analytics/error-breakdown?email=${encodeURIComponent(user.email)}&days=30`
            ),
            fetch(
              `${API_BASE_URL}/api/analytics/heatmap?email=${encodeURIComponent(user.email)}&weeks=5`
            ),
            fetch(
              `${API_BASE_URL}/api/analytics/insights?email=${encodeURIComponent(user.email)}`
            ),
            fetch(
              `${API_BASE_URL}/api/analytics/recommendations?email=${encodeURIComponent(user.email)}`
            ),
            fetch(
              `${API_BASE_URL}/api/analysis/history?email=${encodeURIComponent(user.email)}&limit=100`
            ),
          ]);

        const [summaryData, trendData, errorData, heatmapData, insightsData, recsData, historyData] =
          await Promise.all([
            summaryRes.json(),
            trendRes.json(),
            errorRes.json(),
            heatmapRes.json(),
            insightsRes.json(),
            recsRes.json(),
            historyRes.json(),
          ]);

        setSummary(summaryData);
        setScoreTrend(trendData);
        setErrorBreakdown(errorData);
        setHeatmap(heatmapData);
        setInsights(insightsData);
        setRecommendations(recsData);
        setSessionHistory(historyData.history || []);
      } catch (error) {
        console.error("Error fetching analytics:", error);
        toast({
          title: "Error",
          description: "Failed to load analytics data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [user?.email, toast]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (!summary || summary.total_sessions < 2) {
    return (
      <MainLayout>
        <div className="flex h-96 items-center justify-center">
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-lg text-gray-600">
                Record at least 2 sessions to unlock your analytics dashboard.
              </p>
            </CardContent>
          </Card>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Metrics Row */}
        <MetricsRow summary={summary} />

        {/* Charts Row */}
        <ChartsRow scoreTrend={scoreTrend} errorBreakdown={errorBreakdown} />

        {/* Bottom Row */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <InsightsPanel insights={insights} />
          <RecommendationsPanel recommendations={recommendations} />
          <HeatmapCard heatmap={heatmap} />
        </div>

        {/* Session History Table */}
        <SessionHistoryTable
          sessions={sessionHistory}
          onReview={(session) => {
            setSelectedSession(session);
            setShowReviewModal(true);
          }}
        />

        {/* Review Modal */}
        {selectedSession && (
          <SessionReviewModal
            session={selectedSession}
            open={showReviewModal}
            onOpenChange={setShowReviewModal}
          />
        )}
      </div>
    </MainLayout>
  );
};

const MainLayout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
    <Navbar />
    <main className="pt-24 lg:pt-32 pb-20">
      <div className="p-4 md:p-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900">Your Analytics</h1>
            <p className="mt-2 text-gray-600">
              Track your progress and insights
            </p>
          </div>
          {children}
        </div>
      </div>
    </main>
  </div>
);

// === METRICS ROW ===
const MetricsRow = ({ summary }: { summary: AnalyticsSummary }) => {
  const improvementIsPositive = (summary.improvement_pct ?? 0) >= 0;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
      {/* Current Score */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-600">
            Current Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-purple-600">
            {summary.current_score.toFixed(1)}/5
          </div>
          <div className="mt-2 flex items-center gap-1 text-sm">
            {improvementIsPositive ? (
              <>
                <TrendingUp className="h-4 w-4 text-green-600" />
                <span className="text-green-600">
                  {Math.abs(summary.improvement_pct ?? 0).toFixed(1)}%
                </span>
              </>
            ) : (
              <>
                <TrendingDown className="h-4 w-4 text-red-600" />
                <span className="text-red-600">
                  {Math.abs(summary.improvement_pct ?? 0).toFixed(1)}%
                </span>
              </>
            )}
            <span className="text-gray-500">vs last week</span>
          </div>
        </CardContent>
      </Card>

      {/* 7-day Average */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-600">
            7-Day Avg
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-blue-600">
            {summary.avg_7day.toFixed(1)}
          </div>
          <p className="mt-2 text-xs text-gray-500">Last 7 days</p>
        </CardContent>
      </Card>

      {/* 30-day Average */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-600">
            30-Day Avg
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-indigo-600">
            {summary.avg_30day.toFixed(1)}
          </div>
          <p className="mt-2 text-xs text-gray-500">Last 30 days</p>
        </CardContent>
      </Card>

      {/* Total Sessions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-600">
            Sessions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-green-600">
            {summary.total_sessions}
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {summary.total_speaking_minutes.toFixed(1)}m speaking
          </p>
        </CardContent>
      </Card>

      {/* Practice Streak */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-600">
            Streak
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2">
            <Flame className="h-6 w-6 text-orange-500" />
            <span className="text-3xl font-bold text-orange-600">
              {summary.current_streak}
            </span>
          </div>
          <p className="mt-2 text-xs text-gray-500">consecutive days</p>
        </CardContent>
      </Card>
    </div>
  );
};

// === CHARTS ROW ===
const ChartsRow = ({
  scoreTrend,
  errorBreakdown,
}: {
  scoreTrend: ScoreTrendPoint[];
  errorBreakdown: ErrorBreakdown | null;
}) => {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* Score Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Score Trend</CardTitle>
        </CardHeader>
        <CardContent>
          {scoreTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={scoreTrend}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#534AB7" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#534AB7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  interval={Math.max(0, Math.floor(scoreTrend.length / 6))}
                />
                <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #ccc",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#534AB7"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorScore)"
                  dot={false}
                  activeDot={{
                    r: 6,
                    fill: "#534AB7",
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No data yet
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Breakdown Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Error Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          {errorBreakdown && Object.values(errorBreakdown).some(v => v > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  {
                    name: "Articles",
                    value: errorBreakdown.articles,
                    fill: "#AFA9EC",
                  },
                  {
                    name: "Tense",
                    value: errorBreakdown.tense,
                    fill: "#5DCAA5",
                  },
                  {
                    name: "Preposition",
                    value: errorBreakdown.preposition,
                    fill: "#F0997B",
                  },
                  {
                    name: "Agreement",
                    value: errorBreakdown.agreement,
                    fill: "#85B7EB",
                  },
                  {
                    name: "Other",
                    value: errorBreakdown.other,
                    fill: "#C0DD97",
                  },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" label={{ position: "top" }}>
                  {[
                    { fill: "#AFA9EC" },
                    { fill: "#5DCAA5" },
                    { fill: "#F0997B" },
                    { fill: "#85B7EB" },
                    { fill: "#C0DD97" },
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No data yet
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// === INSIGHTS PANEL ===
const InsightsPanel = ({ insights }: { insights: Insight | null }) => (
  <Card>
    <CardHeader>
      <CardTitle className="text-lg">Insights</CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      {insights?.most_improved_area && (
        <div>
          <p className="text-sm font-semibold text-gray-600">
            Most Repeated Error
          </p>
          <p className="mt-1 text-lg font-bold text-green-600">
            {insights.most_improved_area.category}
          </p>
          <p className="text-xs text-gray-500">
            {insights.most_improved_area.improvement_pct.toFixed(1)}% of errors
          </p>
        </div>
      )}

      {insights?.most_repeated_error && (
        <div>
          <p className="text-sm font-semibold text-gray-600">Top Error Type</p>
          <p className="mt-1 text-lg font-bold text-red-600">
            {insights.most_repeated_error.category}
          </p>
          <p className="text-xs text-gray-500">
            {insights.most_repeated_error.count} occurrences
          </p>
        </div>
      )}

      {insights?.peak_time && (
        <div>
          <p className="text-sm font-semibold text-gray-600">Peak Time</p>
          <div className="mt-1 flex items-center gap-2">
            <Clock className="h-5 w-5 text-blue-600" />
            <p className="text-lg font-bold text-blue-600 capitalize">
              {insights.peak_time}
            </p>
          </div>
        </div>
      )}

      {insights?.best_session && (
        <div>
          <p className="text-sm font-semibold text-gray-600">Best Session</p>
          <p className="mt-1 text-lg font-bold text-purple-600">
            {insights.best_session.score.toFixed(1)}/5
          </p>
          <p className="text-xs text-gray-500">
            {new Date(insights.best_session.date).toLocaleDateString()}
          </p>
        </div>
      )}
    </CardContent>
  </Card>
);

// === RECOMMENDATIONS PANEL ===
const RecommendationsPanel = ({
  recommendations,
}: {
  recommendations: Recommendation[];
}) => (
  <Card>
    <CardHeader>
      <CardTitle className="text-lg">Recommendations</CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      {recommendations.length > 0 ? (
        recommendations.map((rec, idx) => (
          <div key={idx} className="border-l-4 border-purple-600 pl-4">
            <p className="text-xs font-semibold uppercase tracking-widest text-purple-600">
              {rec.label}
            </p>
            <p className="mt-1 text-sm text-gray-700">{rec.message}</p>
          </div>
        ))
      ) : (
        <p className="text-sm text-gray-500">Keep up the great work!</p>
      )}
    </CardContent>
  </Card>
);

// === HEATMAP CARD ===
const HeatmapCard = ({ heatmap }: { heatmap: HeatmapData[] }) => {
  const maxCount = Math.max(
    ...heatmap.flatMap((d) => d.counts),
    1
  );

  const getColor = (count: number) => {
    if (count === 0) return "bg-gray-100";
    if (count === 1) return "bg-purple-200";
    if (count === 2) return "bg-purple-400";
    return "bg-purple-700";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Practice Heatmap</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {heatmap.map((row) => (
            <div key={row.day} className="flex items-center gap-2">
              <div className="w-12 text-xs font-semibold text-gray-600">
                {row.day}
              </div>
              <div className="flex gap-1">
                {row.counts.map((count, idx) => (
                  <div
                    key={idx}
                    className={`h-6 w-6 rounded text-xs flex items-center justify-center text-white font-semibold ${getColor(count)}`}
                    title={`${count} sessions`}
                  >
                    {count > 0 ? count : ""}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-center gap-2 text-xs text-gray-500">
          <span>Less</span>
          <div className="flex gap-1">
            {[
              "bg-gray-100",
              "bg-purple-200",
              "bg-purple-400",
              "bg-purple-700",
            ].map((color) => (
              <div key={color} className={`h-3 w-3 rounded ${color}`} />
            ))}
          </div>
          <span>More</span>
        </div>
      </CardContent>
    </Card>
  );
};

// === SESSION HISTORY TABLE ===
const SessionHistoryTable = ({
  sessions,
  onReview,
}: {
  sessions: SessionData[];
  onReview: (session: SessionData) => void;
}) => {
  const getScoreBadgeColor = (score: number) => {
    if (score >= 4.0) return "bg-green-100 text-green-800";
    if (score >= 3.0) return "bg-amber-100 text-amber-800";
    return "bg-red-100 text-red-800";
  };

  const getTopErrors = (errorSummary: Record<string, number>) => {
    const entries = Object.entries(errorSummary)
      .filter(([key]) => key !== "total_errors")
      .sort(([, a], [, b]) => b - a)
      .slice(0, 2);

    return entries.map(([key]) => key.replace(/_/g, " ").split(" ")[0]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Session History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-gray-600">
                <th className="px-4 py-3 text-left font-semibold">
                  Date & Time
                </th>
                <th className="px-4 py-3 text-left font-semibold">Transcript</th>
                <th className="px-4 py-3 text-left font-semibold">Score</th>
                <th className="px-4 py-3 text-left font-semibold">Errors</th>
                <th className="px-4 py-3 text-left font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length > 0 ? (
                sessions.map((session) => (
                  <tr key={session.id} className="border-b">
                    <td className="px-4 py-3 whitespace-nowrap text-gray-700">
                      {new Date(session.createdAt).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="px-4 py-3 max-w-xs text-gray-700">
                      <p className="truncate text-xs">
                        {session.transcript?.substring(0, 80) || "N/A"}...
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={getScoreBadgeColor(session.score)}>
                        {session.score.toFixed(1)}/5
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {getTopErrors(session.error_summary || {}).map(
                          (error, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-xs"
                            >
                              {error}
                            </Badge>
                          )
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onReview(session)}
                      >
                        Review
                      </Button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    No sessions yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

// === SESSION REVIEW MODAL ===
const SessionReviewModal = ({
  session,
  open,
  onOpenChange,
}: {
  session: SessionData;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) => {
  const getScoreBadgeColor = (score: number) => {
    if (score >= 4.0) return "bg-green-100 text-green-800";
    if (score >= 3.0) return "bg-amber-100 text-amber-800";
    return "bg-red-100 text-red-800";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Session Review</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Score Badge */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-700">Score</h3>
            <Badge className={getScoreBadgeColor(session.score)}>
              {session.score.toFixed(1)}/5
            </Badge>
          </div>

          {/* Session Details */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-semibold text-gray-700">Date</p>
              <p className="mt-1 text-gray-600">
                {new Date(session.createdAt).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="font-semibold text-gray-700">Duration</p>
              <p className="mt-1 text-gray-600">
                {(session.duration / 60).toFixed(1)} minutes
              </p>
            </div>
          </div>

          {/* Transcript */}
          <div>
            <h3 className="font-semibold text-gray-700">Transcript</h3>
            <p className="mt-2 rounded bg-gray-100 p-3 text-gray-700">
              {session.transcript}
            </p>
          </div>

          {/* Correction */}
          {session.corrected_text && (
            <div>
              <h3 className="font-semibold text-gray-700">Grammar Correction</h3>
              <p className="mt-2 rounded bg-blue-50 p-3 text-gray-700">
                {session.corrected_text}
              </p>
            </div>
          )}

          {/* Error Breakdown */}
          {session.error_summary && (
            <div>
              <h3 className="font-semibold text-gray-700">Error Breakdown</h3>
              <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
                {Object.entries(session.error_summary).map(([key, value]) => (
                  <div
                    key={key}
                    className="rounded bg-gray-100 p-2 text-center"
                  >
                    <p className="font-semibold text-gray-700">
                      {String(value)}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">
                      {key.replace(/_/g, " ")}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// === SKELETON LOADER ===
const DashboardSkeleton = () => (
  <MainLayout>
    <div className="space-y-6 animate-pulse">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="h-8 w-24 rounded bg-gray-200"></div>
              <div className="mt-2 h-4 w-32 rounded bg-gray-200"></div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {[...Array(2)].map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="h-64 rounded bg-gray-200"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  </MainLayout>
);

export default Dashboard;
