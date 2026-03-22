import { motion } from "framer-motion";
import { Brain, MessageSquareText, Target, Lightbulb, CheckCircle, BarChart3, FileDown, TrendingUp } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    description: "Advanced neural networks analyze speech patterns with exceptional accuracy.",
  },
  {
    icon: Target,
    title: "Grammar Scoring",
    description: "Comprehensive grammar score from 0-5 based on grammatical correctness.",
  },
  {
    icon: MessageSquareText,
    title: "Instant Transcription",
    description: "Convert spoken audio to text using state-of-the-art Whisper model.",
  },
  {
    icon: CheckCircle,
    title: "Smart Corrections",
    description: "AI-powered suggestions with side-by-side original and corrected text.",
  },
  {
    icon: BarChart3,
    title: "Detailed Feedback",
    description: "Comprehensive insights to improve your spoken English skills.",
  },
  {
    icon: FileDown,
    title: "Downloadable Report",
    description: "Export complete analysis as PDF for future reference.",
  },
];

const FeaturesSection = () => {
  return (
    <section id="features" className="relative py-24 lg:py-32 bg-white dark:bg-slate-900">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-50/50 to-transparent dark:via-slate-800/50" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
            <span className="text-slate-900 dark:text-white">Powerful </span>
            <span className="gradient-text">AI Features</span>
          </h2>
          <p className="text-slate-600 dark:text-slate-300 text-lg leading-relaxed">
            Everything you need to analyze and improve your spoken English grammar with cutting-edge AI technology.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              className="group"
            >
              <div className="gradient-border h-full p-6 lg:p-8">
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-200 dark:border-blue-800 flex items-center justify-center mb-6 group-hover:from-blue-500/20 group-hover:to-indigo-500/20 transition-colors duration-300">
                  <feature.icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>

                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
