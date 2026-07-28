/**
 * All possible states of the Living Orb.
 *
 * Every animation, transition, and interaction derives from this enum.
 * New states must not be added without a corresponding update to OrbStateMachine.
 */
export enum OrbState {
  Initializing = "initializing",
  Idle = "idle",
  Hover = "hover",
  Active = "active",
  Processing = "processing",
  Streaming = "streaming",
  Success = "success",
  Notification = "notification",
  Sleeping = "sleeping",
  Error = "error",
}
