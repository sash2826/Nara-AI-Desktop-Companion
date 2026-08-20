import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { LoginPage } from "@/pages/LoginPage";
import { useAuth } from "@/hooks/useAuth";

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * Gates the main application behind Azure AD authentication.
 * - While checking the keychain: shows a minimal splash.
 * - If unauthenticated: renders LoginPage.
 * - If authenticated: renders children.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="flex flex-col items-center gap-3"
        >
          <Loader2 size={20} className="animate-spin text-muted-foreground/50" />
          <p className="text-xs text-muted-foreground/40">Starting…</p>
        </motion.div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
