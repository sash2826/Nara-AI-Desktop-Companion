import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface AssistantAvatarProps {
  size?: "sm" | "md" | "lg";
  isActive?: boolean;
  className?: string;
}

const SIZE_CLASSES = {
  sm: "h-7 w-7 text-xs",
  md: "h-9 w-9 text-sm",
  lg: "h-12 w-12 text-base",
};

export function AssistantAvatar({
  size = "md",
  isActive = false,
  className,
}: AssistantAvatarProps) {
  return (
    <div className={cn("relative flex-shrink-0", className)}>
      <motion.div
        whileHover={{ scale: 1.05 }}
        transition={{ type: "spring", stiffness: 400, damping: 20 }}
        className={cn(
          "flex items-center justify-center rounded-full bg-primary font-bold text-primary-foreground",
          SIZE_CLASSES[size]
        )}
        aria-hidden="true"
      >
        AI
      </motion.div>

      {/* Online indicator dot */}
      {isActive && (
        <span
          className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-background bg-success"
          aria-hidden="true"
        />
      )}
    </div>
  );
}
