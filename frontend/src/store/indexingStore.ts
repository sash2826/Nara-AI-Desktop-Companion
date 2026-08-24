import { create } from "zustand";
import { IPCClient } from "@/services/ipc/IPCClient";
import type { IndexingStatus } from "@/services/ipc/IPCClient";

export interface IndexingTaskState {
  taskId: string;
  workspacePath: string;
  status: IndexingStatus | null;
  polling: boolean;
}

interface IndexingStore {
  tasks: IndexingTaskState[];
  startIndex: (workspacePath: string) => Promise<void>;
  stopTask: (taskId: string) => Promise<void>;
}

// Module-level interval map — lives outside React so unmounting a component
// never stops an in-progress poll.
const intervalMap = new Map<string, ReturnType<typeof setInterval>>();

function clearTaskInterval(taskId: string) {
  const handle = intervalMap.get(taskId);
  if (handle !== undefined) {
    clearInterval(handle);
    intervalMap.delete(taskId);
  }
}

function startPolling(
  taskId: string,
  set: (fn: (s: IndexingStore) => Partial<IndexingStore>) => void
) {
  const handle = setInterval(async () => {
    try {
      const status = await IPCClient.getIndexingStatus(taskId);
      const isDone =
        status.status !== "running" && status.status !== "queued" && status.status !== "cancelled";
      const isCancelled = status.status === "cancelled";

      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.taskId === taskId ? { ...t, status, polling: !isDone && !isCancelled } : t
        ),
      }));

      if (isDone || isCancelled) {
        clearTaskInterval(taskId);
      }
    } catch {
      clearTaskInterval(taskId);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.taskId === taskId ? { ...t, polling: false } : t)),
      }));
    }
  }, 2000);

  intervalMap.set(taskId, handle);
}

export const useIndexingStore = create<IndexingStore>((set) => ({
  tasks: [],

  startIndex: async (workspacePath) => {
    try {
      const response = await IPCClient.indexWorkspace(workspacePath);
      const task: IndexingTaskState = {
        taskId: response.task_id,
        workspacePath,
        status: null,
        polling: true,
      };
      set((state) => ({ tasks: [task, ...state.tasks.slice(0, 9)] }));
      startPolling(response.task_id, set);
    } catch (err) {
      console.error("Failed to start indexing:", err);
    }
  },

  stopTask: async (taskId) => {
    try {
      await IPCClient.cancelIndexing(taskId);
    } catch {
      // ignore — task may have already finished
    }
    clearTaskInterval(taskId);
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.taskId === taskId
          ? { ...t, polling: false, status: t.status ? { ...t.status, status: "cancelled" } : null }
          : t
      ),
    }));
  },
}));
