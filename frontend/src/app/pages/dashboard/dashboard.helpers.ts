import {
  DeviceStatus,
  MessageItem,
  StatusResponse
} from '../../core/models/mqtt.models';

import { formatTelemetryValue } from '../../core/utils/mqtt-message-display.util';

export interface DeviceLatestTelemetry {
  status: string;
  temperature: string;
  humidity: string;
  lastSeenText: string;
}

export type DeviceTelemetryMap = Record<string, DeviceLatestTelemetry>;

export function createInitialStatus(): StatusResponse {
  return {
    connected: false,
    periodic_publishing: false,
    subscriptions: {},
    devices: []
  };
}

export function createInitialDeviceTelemetryState(): DeviceTelemetryMap {
  return {};
}

export function normalizeStatus(status: StatusResponse): StatusResponse {
  return {
    connected: status.connected,
    periodic_publishing: status.periodic_publishing,
    subscriptions: { ...(status.subscriptions ?? {}) },
    devices: status.devices ?? []
  };
}

export function buildDashboardTopics(
  devices: DeviceStatus[],
  fallbackTopics: string[]
): string[] {
  const topics = new Set<string>();

  for (const device of devices ?? []) {
    if (device.topics?.status) {
      topics.add(device.topics.status);
    }

    if (device.topics?.temperatura) {
      topics.add(device.topics.temperatura);
    }

    if (device.topics?.umiditate) {
      topics.add(device.topics.umiditate);
    }

    if (device.topics?.config) {
      topics.add(device.topics.config);
    }
  }

  for (const topic of fallbackTopics) {
    topics.add(topic);
  }

  return Array.from(topics);
}

export function syncTelemetryWithDevices(
  current: DeviceTelemetryMap,
  devices: DeviceStatus[]
): DeviceTelemetryMap {
  const next: DeviceTelemetryMap = { ...current };

  for (const device of devices ?? []) {
    const existing = next[device.client_id];

    next[device.client_id] = {
      status: device.status || existing?.status || '-',
      temperature: existing?.temperature || '-',
      humidity: existing?.humidity || '-',
      lastSeenText: formatLastSeen(device.last_seen)
    };
  }

  return next;
}

export function updateDeviceTelemetryState(
  current: DeviceTelemetryMap,
  newMessages: MessageItem[]
): DeviceTelemetryMap {
  const next: DeviceTelemetryMap = { ...current };

  for (const msg of newMessages) {
    const topicInfo = parseDeviceTopic(msg.topic);

    if (!topicInfo) {
      continue;
    }

    const existing = next[topicInfo.clientId] ?? {
      status: '-',
      temperature: '-',
      humidity: '-',
      lastSeenText: '-'
    };

    if (topicInfo.category === 'status') {
      next[topicInfo.clientId] = {
        ...existing,
        status: formatTelemetryValue(msg.topic, msg.message),
        lastSeenText: formatMessageTimestamp(msg.timestamp)
      };
    }

    if (topicInfo.category === 'temperatura') {
      next[topicInfo.clientId] = {
        ...existing,
        temperature: formatTelemetryValue(msg.topic, msg.message),
        lastSeenText: formatMessageTimestamp(msg.timestamp)
      };
    }

    if (topicInfo.category === 'umiditate') {
      next[topicInfo.clientId] = {
        ...existing,
        humidity: formatTelemetryValue(msg.topic, msg.message),
        lastSeenText: formatMessageTimestamp(msg.timestamp)
      };
    }
  }

  return next;
}

export function getNextActiveTopic(
  currentTopic: string,
  availableTopics: string[]
): string {
  if (currentTopic && availableTopics.includes(currentTopic)) {
    return currentTopic;
  }

  const firstTelemetryTopic = availableTopics.find(
    (topic) =>
      topic.includes('/temperatura') ||
      topic.includes('/umiditate') ||
      topic.includes('/status')
  );

  return firstTelemetryTopic ?? availableTopics[0] ?? '';
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

export function topicMatchesFilter(topicFilter: string, topic: string): boolean {
  if (!topicFilter) {
    return false;
  }

  const filterParts = topicFilter.split('/');
  const topicParts = topic.split('/');

  for (let index = 0; index < filterParts.length; index++) {
    const filterPart = filterParts[index];

    if (filterPart === '#') {
      return true;
    }

    if (index >= topicParts.length) {
      return false;
    }

    if (filterPart === '+') {
      continue;
    }

    if (filterPart !== topicParts[index]) {
      return false;
    }
  }

  return filterParts.length === topicParts.length;
}

function parseDeviceTopic(topic: string): { clientId: string; category: string } | null {
  const parts = topic.split('/');

  if (parts.length !== 3) {
    return null;
  }

  if (parts[0] !== 'licenta') {
    return null;
  }

  return {
    clientId: parts[1],
    category: parts[2]
  };
}

function formatLastSeen(lastSeen: number | null | undefined): string {
  if (!lastSeen) {
    return '-';
  }

  return formatMessageTimestamp(lastSeen);
}

function formatMessageTimestamp(timestamp: number): string {
  const milliseconds = timestamp > 1000000000000 ? timestamp : timestamp * 1000;

  return new Date(milliseconds).toLocaleTimeString('ro-RO', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}