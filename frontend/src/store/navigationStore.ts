import { create } from "zustand";
import type { NavItemId } from "@/types/navigation";

interface NavigationStore {
  activeItem: NavItemId;
  setActiveItem: (id: NavItemId) => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  activeItem: "home",
  setActiveItem: (id) => set({ activeItem: id }),
}));
