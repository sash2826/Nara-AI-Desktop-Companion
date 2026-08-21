import { motion } from "framer-motion";
import { BookOpen, Search } from "lucide-react";
import volvoLogo from "@/assets/volvo-logo.svg";

interface EmptyChatStateProps {
  onQuickPrompt: (text: string) => void;
}

const CARDS = [
  {
    icon: BookOpen,
    title: "Ask & Create",
    subtitle: "Best for everyday AI tasks:",
    bullets: [
      "Write, summarise, and translate documents",
      "Brainstorm ideas and draft reports",
      "Explain concepts and answer questions",
    ],
    prompt: "What can you help me with?",
    colorClass:
      "bg-[hsl(var(--color-neutral-0))] shadow-elevation-2 border-[hsl(var(--info)/0.4)] hover:border-[hsl(var(--info)/0.7)] dark:bg-[hsl(var(--info)/0.18)] dark:shadow-none dark:border-[hsl(var(--info)/0.35)] dark:hover:border-[hsl(var(--info)/0.55)]",
    iconClass: "text-[hsl(var(--info))]",
    subtitleClass: "text-[hsl(var(--info)/0.7)] dark:text-muted-foreground",
    bulletClass: "text-[hsl(var(--info)/0.85)] dark:text-muted-foreground/80",
    titleClass: "text-[hsl(var(--info))] dark:text-foreground",
  },
  {
    icon: Search,
    title: "Search Your Workspace",
    subtitle: "Best for finding information:",
    bullets: [
      "Query across all your indexed files",
      "Retrieve relevant sections from documents",
      "Explore connections between your files",
    ],
    prompt: "Search my documents for ",
    colorClass:
      "bg-[hsl(var(--color-neutral-0))] shadow-elevation-2 border-amber-300 hover:border-amber-500 dark:bg-amber-950/60 dark:shadow-none dark:border-amber-700/50 dark:hover:border-amber-500/70",
    iconClass: "text-amber-600 dark:text-amber-400",
    subtitleClass: "text-amber-800/70 dark:text-muted-foreground",
    bulletClass: "text-amber-950/70 dark:text-muted-foreground/80",
    titleClass: "text-amber-950 dark:text-foreground",
  },
] as const;

export function EmptyChatState({ onQuickPrompt }: EmptyChatStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex h-full flex-col items-center justify-between px-8 py-10 text-center select-none"
    >
      {/* VOLVO wordmark — top */}
      <motion.img
        src={volvoLogo}
        alt="Volvo"
        aria-hidden="true"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.05, ease: "easeOut" }}
        className="h-6 w-auto opacity-30 dark:invert"
      />

      {/* Feature cards — centre */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.2 }}
        className="grid grid-cols-2 gap-3 w-full max-w-xl"
      >
        {CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <button
              key={card.title}
              onClick={() => onQuickPrompt(card.prompt)}
              className={`
                text-left rounded-xl border p-4 transition-all duration-200
                cursor-pointer group
                ${card.colorClass}
              `}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className={`text-sm font-semibold leading-tight ${card.titleClass}`}>
                  {card.title}
                </span>
                <Icon size={15} className={`shrink-0 mt-0.5 ${card.iconClass}`} />
              </div>
              <p className={`text-xs mb-2.5 ${card.subtitleClass}`}>{card.subtitle}</p>
              <ul className="space-y-1.5">
                {card.bullets.map((b) => (
                  <li key={b} className={`flex items-start gap-1.5 text-xs ${card.bulletClass}`}>
                    <span className="mt-0.5 shrink-0 opacity-50">•</span>
                    {b}
                  </li>
                ))}
              </ul>
            </button>
          );
        })}
      </motion.div>

      {/* Tagline — bottom (opposite end to the wordmark) */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.35, delay: 0.35 }}
        className="text-xs text-muted-foreground/50 leading-relaxed"
      >
        Powered by Volvo Gen AI Hub
      </motion.p>
    </motion.div>
  );
}
