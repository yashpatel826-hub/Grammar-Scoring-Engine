import { motion } from "framer-motion";

const steps = [
  {
    step: "01",
    title: "Upload Audio",
    description: "Drop your .wav audio file or browse to select",
  },
  {
    step: "02",
    title: "AI Transcription",
    description: "Advanced AI converts your speech to text accurately",
  },
  {
    step: "03",
    title: "Grammar Evaluation",
    description: "Deep analysis of grammar, structure, and language patterns",
  },
  {
    step: "04",
    title: "Detailed Feedback",
    description: "Get your score, corrections, and improvement suggestions",
  },
];

const HowItWorksSection = () => {
  return (
    <section className="relative py-24 lg:py-32 overflow-hidden">
      <div className="absolute inset-0 bg-card/20" />
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border/50 to-transparent" />

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
            <span className="text-foreground">How It </span>
            <span className="gradient-text">Works</span>
          </h2>
          <p className="text-muted-foreground text-lg">
            Simple four-step process to analyze your spoken English
          </p>
        </motion.div>

        {/* Steps - vertical list */}
        <div className="max-w-2xl mx-auto space-y-6">
          {steps.map((step, index) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.12, duration: 0.5 }}
              className="flex items-start gap-5"
            >
              <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 border border-primary/20 flex items-center justify-center">
                <span className="text-lg font-bold gradient-text">{step.step}</span>
              </div>
              <div className="pt-1">
                <h3 className="text-lg font-semibold text-foreground mb-1">
                  {step.title}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
