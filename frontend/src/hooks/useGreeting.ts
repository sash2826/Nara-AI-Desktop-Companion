import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";

function greetingForHour(hour: number): string {
  if (hour < 5) return "Good night";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  if (hour < 22) return "Good evening";
  return "Good night";
}

/** Time-of-day greeting, optionally addressed to the signed-in user's first name. */
export function useGreeting(): string {
  const userDisplayName = useAuthStore((s) => s.userDisplayName);
  const [hour, setHour] = useState(() => new Date().getHours());

  useEffect(() => {
    const id = setInterval(() => setHour(new Date().getHours()), 60_000);
    return () => clearInterval(id);
  }, []);

  const greeting = greetingForHour(hour);
  const firstName = userDisplayName?.trim().split(/\s+/)[0];

  return firstName ? `${greeting}, ${firstName}` : greeting;
}
