/**
 * All possible states of the Living Orb.
 *
 * Every animation, transition, and interaction derives from this enum.
 * New states must not be added without a corresponding update to OrbStateMachine.
 */
export enum OrbState {
  Idle = "idle",
  Hover = "hover",
  Thinking = "thinking",
  Listening = "listening",
  Speaking = "speaking",
  Notification = "notification",
  Error = "error",
  Sleeping = "sleeping",
}
