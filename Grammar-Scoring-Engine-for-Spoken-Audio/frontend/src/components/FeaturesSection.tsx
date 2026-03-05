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
    <section id="features" className="relative py-24 lg:py-32 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-muted/10 to-background" />

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
            <span className="text-foreground">Powerful </span>
            <span className="gradient-text">Features</span>
          </h2>
          <p className="text-muted-foreground text-lg">
            Everything you need to analyze and improve your spoken English grammar.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.08, duration: 0.5 }}
              className="group"
            >
              <div className="relative rounded-2xl p-6 h-full border border-border/40 bg-card/50 hover:border-primary/30 transition-all duration-300">
                {/* Icon */}
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/15 to-secondary/15 border border-primary/10 flex items-center justify-center mb-5 group-hover:from-primary/25 group-hover:to-secondary/25 transition-colors duration-300">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>

                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
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
