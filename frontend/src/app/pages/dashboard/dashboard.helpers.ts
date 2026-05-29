import { MessageItem, StatusResponse } from '../../core/models/mqtt.models';

export interface LatestTelemetryState {
  latestStatus: string;
  latestTemperature: string;
  latestHumidity: string;
}

export function createInitialStatus(): StatusResponse {
  return {
    connected: false,
    periodic_publishing: false,
    subscriptions: {}
  };
}

export function createInitialTelemetryState(): LatestTelemetryState {
  return {
    latestStatus: '-',
    latestTemperature: '-',
    latestHumidity: '-'
  };
}

export function normalizeStatus(status: StatusResponse): StatusResponse {
  return {
    connected: status.connected,
    periodic_publishing: status.periodic_publishing,
    subscriptions: { ...(status.subscriptions ?? {}) }
  };
}

export function updateTelemetryState(
  current: LatestTelemetryState,
  newMessages: MessageItem[]
): LatestTelemetryState {
  const next = { ...current };

  for (const msg of newMessages) {
    if (msg.topic === 'licenta/pico/status') {
      next.latestStatus = msg.message;
    }

    if (msg.topic === 'licenta/pico/temperatura') {
      next.latestTemperature = msg.message;
    }

    if (msg.topic === 'licenta/pico/umiditate') {
      next.latestHumidity = msg.message;
    }
  }

  return next;
}

export function getNextActiveTopic(
  subscriptions: Record<string, number>,
  subscribeTopic: string,
  activeMessageTopic: string
): string {
  const subscribedTopics = Object.keys(subscriptions);

  if (
    activeMessageTopic &&
    subscriptions[activeMessageTopic] !== undefined
  ) {
    return activeMessageTopic;
  }

  if (subscriptions[subscribeTopic] !== undefined) {
    return subscribeTopic;
  }

  return subscribedTopics.length > 0 ? subscribedTopics[0] : '';
}

export function isTopicSubscribed(
  subscriptions: Record<string, number>,
  topic: string
): boolean {
  return subscriptions[topic] !== undefined;
}

export function hasSameSubscriptionQos(
  subscriptions: Record<string, number>,
  topic: string,
  qos: number
): boolean {
  const currentQos = subscriptions[topic];

  if (currentQos === undefined || currentQos === null) {
    return false;
  }

  return Number(currentQos) === Number(qos);
}

export function getSubscriptionQos(
  subscriptions: Record<string, number>,
  topic: string
): number | null {
  const qos = subscriptions[topic];
  return qos === undefined ? null : Number(qos);
}