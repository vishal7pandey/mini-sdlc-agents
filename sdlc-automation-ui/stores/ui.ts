import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UIState = {
  isSidebarOpen: boolean;
  activeRoute: string;
  selectedAgentId: string;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveRoute: (route: string) => void;
  setSelectedAgentId: (id: string) => void;
};

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isSidebarOpen: true,
      activeRoute: "/",
      selectedAgentId: "finalize",
      toggleSidebar: () =>
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSidebarOpen: (open) => set({ isSidebarOpen: open }),
      setActiveRoute: (route) => set({ activeRoute: route }),
      setSelectedAgentId: (id) => set({ selectedAgentId: id }),
    }),
    {
      name: "ui-storage",
    },
  ),
);
