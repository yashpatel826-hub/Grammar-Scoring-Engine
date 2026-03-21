import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Upload, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-background" />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-t from-secondary/15 via-primary/10 to-transparent blur-3xl rounded-full" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-hero-glow opacity-40" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center pt-20">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-border/60 bg-muted/30 backdrop-blur-sm mb-10"
        >
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-sm text-muted-foreground">AI-Powered Grammar Analysis</span>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.7 }}
          className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold leading-tight mb-8"
        >
          <span className="text-foreground">Analyze Your Spoken</span>
          <br />
          <span className="gradient-text">English with AI</span>
        </motion.h1>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="text-base sm:text-lg text-muted-foreground max-w-xl mx-auto mb-10 leading-relaxed"
        >
          Get grammar score, corrections, and intelligent feedback instantly.
          <br className="hidden sm:block" />
          Perfect your spoken English with advanced AI technology.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl mx-auto mb-20"
        >
          <div className="rounded-2xl border border-border/50 bg-card/30 p-5 text-left">
            <Link to="/upload">
              <Button
                size="lg"
                className="w-full bg-gradient-to-r from-primary to-secondary text-primary-foreground text-base px-8 py-6 rounded-full hover:opacity-90 transition-all duration-300 shadow-lg shadow-primary/20"
              >
                <Upload className="mr-2 w-5 h-5" />
                Upload Audio
              </Button>
            </Link>
            <p className="text-sm text-muted-foreground mt-3">
              Evaluate my own recording.
            </p>
          </div>

          <div className="rounded-2xl border border-border/50 bg-card/30 p-5 text-left">
            <Link to="/upload?mode=demo">
              <Button
                size="lg"
                variant="outline"
                className="w-full border-border/60 text-foreground hover:bg-muted/30 text-base px-8 py-6 rounded-full transition-all duration-300"
              >
                Try Demo
              </Button>
            </Link>
            <p className="text-sm text-muted-foreground mt-3">
              See how the system works with sample audio.
            </p>
          </div>
        </motion.div>

        {/* Microphone Icon */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7, duration: 0.8, ease: "easeOut" }}
          className="flex justify-center"
        >
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/40 to-secondary/40 rounded-full blur-2xl scale-150" />
            <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full bg-gradient-to-br from-primary/20 to-secondary/30 border border-primary/20 flex items-center justify-center backdrop-blur-sm">
              <Mic className="w-12 h-12 sm:w-14 sm:h-14 text-primary" />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;
