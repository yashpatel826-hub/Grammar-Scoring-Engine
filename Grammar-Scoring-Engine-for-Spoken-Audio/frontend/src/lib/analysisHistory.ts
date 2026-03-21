export type PredictResponse = {
  success: boolean;
  filename: string;
  duration: number;
  transcript: string;
  corrected_text?: string;
  correction_changed?: boolean;
  correction_available?: boolean;
  correction_error?: string | null;
  errors?: Array<{
    position?: number;
    type?: string;
    original?: string;
    corrected?: string;
  }>;
  suggestions?: string[];
  error_summary?: {
    total_errors: number;
    [key: string]: number | string;
  };
  score: number;
  predicted_class: number;
  confidence: number;
  processing_time: number;
};

export type AnalysisRecord = PredictResponse & {
  id: string;
  createdAt: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export const getAnalysisHistory = async (email: string): Promise<AnalysisRecord[]> => {
  const response = await fetch(`${API_BASE_URL}/api/analysis/history?email=${encodeURIComponent(email)}`);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload?.detail || "Failed to load analysis history");
  }

  return Array.isArray(payload?.history) ? (payload.history as AnalysisRecord[]) : [];
};

export const saveAnalysisRecord = async (email: string, analysis: PredictResponse): Promise<AnalysisRecord> => {
  const response = await fetch(`${API_BASE_URL}/api/analysis/history`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, analysis }),
  });
  const payload = await response.json().catch(() => ({}));

  if (!response.ok || !payload?.record) {
    throw new Error(payload?.detail || "Failed to save analysis");
  }

  return payload.record as AnalysisRecord;
};
