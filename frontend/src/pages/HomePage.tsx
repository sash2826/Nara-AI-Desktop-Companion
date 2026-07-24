import { Home } from "lucide-react";
import { PlaceholderPage } from "@/components/common/PlaceholderPage";

export function HomePage() {
  return (
    <PlaceholderPage
      title="Home"
      description="Your personal dashboard and recent activity will appear here."
      icon={Home}
    />
  );
}
