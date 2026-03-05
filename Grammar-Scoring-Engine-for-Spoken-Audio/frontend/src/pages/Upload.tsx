import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileAudio, X, Play, Pause, Loader2, Sparkles } from "lucide-react";
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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

const UploadPage = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const navigate = useNavigate();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.includes("audio")) {
      setFile(droppedFile);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setErrorMessage(null);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setIsPlaying(false);
    setErrorMessage(null);
    if (audioRef.current) {
      audioRef.current.pause();
    }
  };

  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      return;
    }

    setErrorMessage(null);
    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      console.log("Uploading file to API:", file.name);
      const response = await fetch(`${API_BASE_URL}/api/predict`, {
        method: "POST",
        body: formData,
      });

      console.log("API Response Status:", response.status);
      console.log("API Response Headers:", response.headers);
      
      let payload;
      try {
        payload = await response.json();
      } catch (parseError) {
        console.error("Failed to parse JSON response:", parseError);
        const text = await response.text();
        console.log("Raw response text:", text);
        throw new Error(`Failed to parse API response: ${text.substring(0, 100)}`);
      }

      console.log("API Response Payload:", payload);

      if (!response.ok) {
        const errorDetail = payload?.detail || payload?.error || "Failed to analyze audio";
        throw new Error(errorDetail);
      }

      if (!payload || typeof payload !== 'object') {
        throw new Error("Invalid response format from API");
      }

      console.log("Navigating to results with payload:", payload);
      navigate("/results", { state: { analysis: payload as PredictResponse } });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unexpected error while analyzing audio";
      console.error("Error during analysis:", errorMsg, error);
      setErrorMessage(errorMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="relative pt-24 lg:pt-32 pb-20 min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-2xl mx-auto mb-10"
          >
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              <span className="text-foreground">Upload Your </span>
              <span className="gradient-text">Audio</span>
            </h1>
            <p className="text-muted-foreground">
              Upload your spoken English audio file and let AI analyze your grammar
            </p>
          </motion.div>

          {/* Upload Area */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-2xl mx-auto"
          >
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 bg-card/30 ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : file
                  ? "border-success/50"
                  : "border-border/50 hover:border-primary/40"
              }`}
            >
              <AnimatePresence mode="wait">
                {!file ? (
                  <motion.div
                    key="upload"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="p-12 lg:p-16 text-center"
                  >
                    <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary/15 to-secondary/20 flex items-center justify-center">
                      <Upload className={`w-7 h-7 ${isDragging ? "text-primary" : "text-primary/70"}`} />
                    </div>

                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      Drop your audio file here
                    </h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      or click to browse
                    </p>

                    <input
                      type="file"
                      accept="audio/*,.wav"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="audio-upload"
                    />
                    <label htmlFor="audio-upload">
                      <Button
                        variant="outline"
                        className="cursor-pointer rounded-full border-border/60 hover:bg-muted/30"
                        asChild
                      >
                        <span>Browse Files</span>
                      </Button>
                    </label>

                    <p className="text-xs text-muted-foreground mt-6">
                      Supports .wav and .mp3 files
                    </p>
                  </motion.div>
                ) : (
                  <motion.div
                    key="preview"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="p-8 lg:p-12"
                  >
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                        <FileAudio className="w-7 h-7 text-primary-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-base font-semibold text-foreground truncate">{file.name}</h4>
                        <p className="text-sm text-muted-foreground">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                      </div>
                      <button onClick={handleRemoveFile} className="p-2 rounded-lg hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-colors">
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="rounded-xl p-4 border border-border/40 bg-muted/20 mb-6">
                      <audio ref={audioRef} src={URL.createObjectURL(file)} onEnded={() => setIsPlaying(false)} className="hidden" />
                      <div className="flex items-center gap-4">
                        <button onClick={togglePlayback} className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center hover:opacity-90 transition-opacity">
                          {isPlaying ? <Pause className="w-4 h-4 text-primary-foreground" /> : <Play className="w-4 h-4 text-primary-foreground ml-0.5" />}
                        </button>
                        <div className="flex-1">
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: isPlaying ? "100%" : "0%" }} transition={{ duration: 10, ease: "linear" }} className="h-full bg-gradient-to-r from-primary to-secondary" />
                          </div>
                        </div>
                      </div>
                    </div>

                    <Button onClick={handleAnalyze} disabled={isAnalyzing || !file} className="w-full bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:opacity-90 h-12 rounded-xl shadow-lg shadow-primary/20">
                      {isAnalyzing ? (
                        <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Analyzing Speech...</>
                      ) : (
                        <><Sparkles className="w-5 h-5 mr-2" />Analyze Speech</>
                      )}
                    </Button>

                    {errorMessage && (
                      <p className="text-sm text-destructive mt-4 text-center">{errorMessage}</p>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Analyzing overlay */}
            <AnimatePresence>
              {isAnalyzing && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
                  <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="rounded-2xl p-12 text-center border border-border/40 bg-card max-w-sm mx-4">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center animate-pulse">
                      <Loader2 className="w-10 h-10 text-primary animate-spin" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">AI Analyzing...</h3>
                    <p className="text-sm text-muted-foreground">Processing your audio with advanced NLP models</p>
                    <div className="mt-6 flex justify-center gap-1">
                      {[0, 1, 2].map((i) => (
                        <motion.div key={i} animate={{ scale: [1, 1.3, 1] }} transition={{ repeat: Infinity, duration: 0.6, delay: i * 0.2 }} className="w-2 h-2 rounded-full bg-primary" />
                      ))}
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default UploadPage;
