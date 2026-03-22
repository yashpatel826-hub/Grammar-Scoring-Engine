import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Upload } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-background" />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-t from-secondary/15 via-primary/10 to-transparent blur-3xl rounded-full" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-hero-glow opacity-40" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center pt-20">
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
          className="flex flex-col sm:flex-row gap-5 justify-center items-center mb-20"
        >
          <Link to="/upload">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
              className="relative inline-flex items-center justify-center gap-2 px-10 py-4 rounded-full text-base font-medium text-white bg-gradient-to-r from-cyan-500 to-blue-600 shadow-[0_0_20px_2px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_6px_rgba(6,182,212,0.45)] transition-all duration-300"
            >
              <Upload className="w-5 h-5 text-white" />
              Upload Audio
            </motion.button>
          </Link>

          <Link to="/upload?mode=demo">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
              className="relative inline-flex items-center justify-center gap-2 px-10 py-4 rounded-full text-base font-medium text-cyan-50 bg-cyan-950/20 border border-cyan-500/40 hover:bg-cyan-900/40 hover:border-cyan-400/80 transition-all duration-300 backdrop-blur-sm"
            >
              Try Demo
            </motion.button>
          </Link>
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;
