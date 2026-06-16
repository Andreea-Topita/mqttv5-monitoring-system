export const DASHBOARD_TOPICS = [
  'licenta/+/status',
  'licenta/+/temperatura',
  'licenta/+/umiditate',
  'licenta/pc/test',
  'licenta/pc/comenzi'
];

export const DEFAULT_PUBLISH_TOPIC = 'licenta/pc/test';
export const DEFAULT_PUBLISH_MESSAGE = 'test message from desktop client';
export const DEFAULT_PUBLISH_QOS = 0;
export const DEFAULT_PERIODIC_INTERVAL = 5;

export const DEFAULT_SUBSCRIBE_TOPIC = 'licenta/+/temperatura';
export const DEFAULT_SUBSCRIBE_QOS = 2;

export const POLLING_INTERVAL_MS = 2000;
export const STATUS_SYNC_PAUSE_MS = 1000;
export const STATUS_REFRESH_DELAY_MS = 1100;
export const PERIODIC_STATUS_REFRESH_DELAY_MS = 400;
export const DEFAULT_HISTORY_PAGE_SIZE = 10;