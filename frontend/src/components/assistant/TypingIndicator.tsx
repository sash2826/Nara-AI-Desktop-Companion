import { motion } from "framer-motion";
import { AssistantAvatar } from "./AssistantAvatar";

const DOT_VARIANTS = {
  initial: { y: 0 },
  animate: { y: -4 },
};

const DOTS = [0, 1, 2];

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      transition={{ duration: 0.18 }}
      className="flex items-end gap-2.5 px-4 py-1"
      aria-label="Assistant is typing"
      aria-live="polite"
    >
      <AssistantAvatar size="sm" />

      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm bg-muted px-3.5 py-2.5">
        {DOTS.map((i) => (
          <motion.span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
            variants={DOT_VARIANTS}
            initial="initial"
            animate="animate"
            transition={{
              duration: 0.5,
              repeat: Infinity,
              repeatType: "reverse",
              delay: i * 0.15,
              ease: "easeInOut",
            }}
            aria-hidden="true"
          />
        ))}
      </div>
    </motion.div>
  );
}
