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
  | "InputStarted"
  | "InputFinished"
  | "ProcessingStarted"
  | "ProcessingFinished"
  | "StreamingStarted"
  | "StreamingFinished"
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

export interface InputStartedEvent {
  readonly type: "InputStarted";
}

export interface InputFinishedEvent {
  readonly type: "InputFinished";
}

export interface ProcessingStartedEvent {
  readonly type: "ProcessingStarted";
}

export interface ProcessingFinishedEvent {
  readonly type: "ProcessingFinished";
}

export interface StreamingStartedEvent {
  readonly type: "StreamingStarted";
}

export interface StreamingFinishedEvent {
  readonly type: "StreamingFinished";
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
  | InputStartedEvent
  | InputFinishedEvent
  | ProcessingStartedEvent
  | ProcessingFinishedEvent
  | StreamingStartedEvent
  | StreamingFinishedEvent
  | NotificationReceivedEvent
  | ErrorOccurredEvent
  | SleepEvent
  | WakeEvent;
