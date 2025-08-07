"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import {
  SparklesIcon,
  CodeBracketIcon,
  ShieldCheckIcon,
  CpuChipIcon,
} from "@heroicons/react/24/outline";

interface ScrollAnimationProps {
  children: React.ReactNode;
}

const ScrollAnimation: React.FC<ScrollAnimationProps> = ({ children }) => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  const y = useTransform(scrollYProgress, [0, 1], ["-20%", "20%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.8, 1, 0.8]);

  return (
    <motion.div ref={ref} style={{ y, opacity, scale }} className="relative">
      {children}
    </motion.div>
  );
};

interface FeatureCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  gradient: string;
  index: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  icon: Icon,
  title,
  description,
  gradient,
  index,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  const x = useTransform(
    scrollYProgress,
    [0, 1],
    index % 2 === 0 ? ["-100px", "100px"] : ["100px", "-100px"],
  );
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0, 1, 1, 0]);

  return (
    <motion.div ref={ref} style={{ x, opacity }} className="group relative">
      <div
        className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-20 transition-all duration-500 rounded-2xl blur-xl"
        style={{ background: `linear-gradient(135deg, ${gradient})` }}
      />
      <div className="relative bg-slate-800/50 border border-slate-700/50 backdrop-blur-xl rounded-2xl p-8 h-full">
        <div
          className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${gradient} p-4 mb-6 shadow-lg`}
        >
          <Icon className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-semibold text-white mb-4 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-purple-400 group-hover:to-pink-400 transition-all duration-300">
          {title}
        </h3>
        <p className="text-gray-300 leading-relaxed text-lg">{description}</p>
      </div>
    </motion.div>
  );
};

const EnhancedFeatures: React.FC = () => {
  const features = [
    {
      icon: CpuChipIcon,
      title: "Agent Network",
      description:
        "Multi-agent AI collaboration with Claude O3, Sonnet 4, and specialized coding agents working together to solve complex problems.",
      gradient: "from-purple-400 to-pink-400",
    },
    {
      icon: CodeBracketIcon,
      title: "Code Generation",
      description:
        "Transform ideas into production-ready code with intelligent AI models that understand context, patterns, and best practices.",
      gradient: "from-blue-400 to-cyan-400",
    },
    {
      icon: ShieldCheckIcon,
      title: "Compliance & Security",
      description:
        "SOC 2 ready platform with JWT tenant isolation, comprehensive audit logging, and enterprise-grade security controls.",
      gradient: "from-green-400 to-emerald-400",
    },
    {
      icon: SparklesIcon,
      title: "Intelligent Assistant",
      description:
        "AI-powered chatbot trained on all Ethical AI Insider content with RAG architecture for contextual responses.",
      gradient: "from-violet-400 to-purple-400",
    },
  ];

  return (
    <section className="relative py-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 to-pink-900/10" />
      <div className="relative max-w-7xl mx-auto">
        <ScrollAnimation>
          <div className="text-center mb-20">
            <motion.h2
              className="text-4xl md:text-5xl font-bold text-white mb-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              Experience the Future of Development
            </motion.h2>
            <motion.p
              className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              Scroll to discover our cutting-edge features that will
              revolutionize your development workflow.
            </motion.p>
          </div>
        </ScrollAnimation>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              gradient={feature.gradient}
              index={index}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default EnhancedFeatures;
