import { motion, AnimatePresence } from "framer-motion";
import { LogIn, AlertCircle, Loader2 } from "lucide-react";
import volvoLogo from "@/assets/volvo-logo.svg";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export function LoginPage() {
  const { login, isLoading, error } = useAuth();

  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center bg-background px-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="flex flex-col items-center gap-4 text-center"
      >
        {/* Volvo logo */}
        <motion.img
          src={volvoLogo}
          alt="Volvo"
          aria-hidden="true"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.05, ease: "easeOut" }}
          className="h-12 w-12 opacity-25 dark:invert"
        />

        {/* Brand name */}
        <motion.h1
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35, delay: 0.15 }}
          className="text-2xl font-semibold tracking-tight text-foreground"
        >
          Nara
        </motion.h1>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35, delay: 0.25 }}
          className="text-sm text-muted-foreground/60"
        >
          Sign in with your Volvo account to continue.
        </motion.p>

        {/* Error message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="flex max-w-xs items-start gap-2 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-left text-xs text-destructive"
            >
              <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Sign-in button */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35, delay: 0.35 }}
          onClick={() => void login()}
          disabled={isLoading}
          className={cn(
            "mt-2 flex items-center gap-2 rounded-full px-6 py-2.5 text-sm font-medium",
            "bg-foreground text-background transition-all duration-fast",
            "hover:bg-foreground/85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-60"
          )}
        >
          {isLoading ? <Loader2 size={15} className="animate-spin" /> : <LogIn size={15} />}
          {isLoading ? "Opening browser…" : "Continue with Microsoft"}
        </motion.button>

        {/* Fine print */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35, delay: 0.45 }}
          className="mt-1 text-2xs text-muted-foreground/40"
        >
          Your browser will open the Volvo Group sign-in page.
        </motion.p>
      </motion.div>
    </div>
  );
}
