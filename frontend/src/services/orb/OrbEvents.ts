/**
 * Strongly typed events that external systems use to drive the Living Orb.
 *
 * Each event carries a discriminant `type` field so consumers can use
 * exhaustive switch statements. Event objects are intentionally value types
 * with no methods — they describe intent, not behaviour.
 *
 * Mapping to OrbStateMachine transitions is the responsibility of OrbController.
 */

export type OrbEventType =
  | "HoverEnter"
  | "HoverLeave"
  | "ThinkingStarted"
  | "ThinkingFinished"
  | "ListeningStarted"
  | "ListeningFinished"
  | "SpeakingStarted"
  | "SpeakingFinished"
  | "NotificationReceived"
  | "ErrorOccurred"
  | "Sleep"
  | "Wake";

export interface HoverEnterEvent {
  readonly type: "HoverEnter";
}

export interface HoverLeaveEvent {
  readonly type: "HoverLeave";
}

export interface ThinkingStartedEvent {
  readonly type: "ThinkingStarted";
}

export interface ThinkingFinishedEvent {
  readonly type: "ThinkingFinished";
}

export interface ListeningStartedEvent {
  readonly type: "ListeningStarted";
}

export interface ListeningFinishedEvent {
  readonly type: "ListeningFinished";
}

export interface SpeakingStartedEvent {
  readonly type: "SpeakingStarted";
}

export interface SpeakingFinishedEvent {
  readonly type: "SpeakingFinished";
}

export interface NotificationReceivedEvent {
  readonly type: "NotificationReceived";
}

export interface ErrorOccurredEvent {
  readonly type: "ErrorOccurred";
  /** Human-readable description of the error — for logging and future UI use. */
  readonly message: string;
}

export interface SleepEvent {
  readonly type: "Sleep";
}

export interface WakeEvent {
  readonly type: "Wake";
}

/** Discriminated union of all orb events. */
export type OrbEvent =
  | HoverEnterEvent
  | HoverLeaveEvent
  | ThinkingStartedEvent
  | ThinkingFinishedEvent
  | ListeningStartedEvent
  | ListeningFinishedEvent
  | SpeakingStartedEvent
  | SpeakingFinishedEvent
  | NotificationReceivedEvent
  | ErrorOccurredEvent
  | SleepEvent
  | WakeEvent;
