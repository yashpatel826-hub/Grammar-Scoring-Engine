import { motion } from "framer-motion";
import { Cpu, Layers, Zap, Globe } from "lucide-react";

const technologies = [
  {
    name: "OpenAI Whisper",
    description: "State-of-the-art speech recognition for accurate transcription",
    icon: Cpu,
  },
  {
    name: "DeBERTa NLP",
    description: "Advanced language model for grammar error detection",
    icon: Layers,
  },
  {
    name: "React + TypeScript",
    description: "Modern frontend framework for seamless user experience",
    icon: Zap,
  },
  {
    name: "RESTful API",
    description: "Efficient backend communication for real-time processing",
    icon: Globe,
  },
];

const AboutSection = () => {
  return (
    <section id="about" className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background to-card/50" />
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-secondary/50 to-transparent" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
              <span className="text-foreground">About This </span>
              <span className="gradient-text">Project</span>
            </h2>
            <p className="text-lg text-muted-foreground mb-6">
              The Grammar Scoring Engine is an innovative AI-powered tool designed to help English language learners improve their spoken grammar. By leveraging cutting-edge machine learning models, we provide accurate, instant feedback on grammatical correctness.
            </p>
            <p className="text-muted-foreground mb-8">
              Our system transcribes spoken audio using OpenAI's Whisper model, then analyzes the text with DeBERTa-based NLP to detect grammatical errors. Users receive a comprehensive score (0-5), detailed corrections, and personalized improvement suggestions.
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6">
              <div className="glass-card rounded-xl p-4 text-center border border-border/50">
                <p className="text-2xl font-bold gradient-text">NLP</p>
                <p className="text-xs text-muted-foreground mt-1">Powered</p>
              </div>
              <div className="glass-card rounded-xl p-4 text-center border border-border/50">
                <p className="text-2xl font-bold gradient-text">ML</p>
                <p className="text-xs text-muted-foreground mt-1">Models</p>
              </div>
              <div className="glass-card rounded-xl p-4 text-center border border-border/50">
                <p className="text-2xl font-bold gradient-text">AI</p>
                <p className="text-xs text-muted-foreground mt-1">Analysis</p>
              </div>
            </div>
          </motion.div>

          {/* Technologies */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-2 gap-4"
          >
            {technologies.map((tech, index) => (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="group glass-card rounded-2xl p-6 border border-border/50 hover:border-primary/50 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center mb-4 group-hover:from-primary/30 group-hover:to-secondary/30 transition-colors">
                  <tech.icon className="w-6 h-6 text-primary" />
                </div>
                <h4 className="font-semibold text-foreground mb-2">{tech.name}</h4>
                <p className="text-sm text-muted-foreground">{tech.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
