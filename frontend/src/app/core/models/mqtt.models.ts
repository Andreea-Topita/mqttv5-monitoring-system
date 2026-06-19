export interface ConnectRequest {
  broker_address: string;
  broker_port: number;
  client_id: string;
  username: string;
  password: string;
  last_will_topic: string;
  last_will_message: string;
  last_will_qos: number;
  last_will_retain: boolean;
  use_tls: boolean;
  tls_insecure: boolean;
}

export interface SubscribeRequest {
  topic: string;
  qos: number;
}

export interface UnsubscribeRequest {
  topic: string;
}

export interface PublishMessageRequest {
  topic: string;
  message: string;
  qos: number;
}

export interface PeriodicPublishRequest {
  topic: string;
  message: string;
  qos: number;
  interval: number;
}

export interface DeviceConfigRequest {
  client_id: string;
  publish_qos: number;
  publish_interval: number;
  message_qos: number;
}

export interface ActionResponse {
  success: boolean;
  message: string;
}

export interface MessageItem {
  id: number;
  topic: string;
  message: string;
  timestamp: number;
}

export interface DeviceTopics {
  status: string;
  temperatura: string;
  umiditate: string;
  config: string;
}

export interface DeviceStatus {
  client_id: string;
  status: string;
  capabilities: string[];
  last_seen: number | null;
  topics: DeviceTopics;
}

export interface StatusResponse {
  connected: boolean;
  periodic_publishing: boolean;
  subscriptions: Record<string, number>;
  devices: DeviceStatus[];
}

export interface MessageHistoryItem {
  id: number;
  topic: string;
  payload: string;
  qos: number;
  direction: 'INBOUND' | 'OUTBOUND';
  source_client_id: string | null;
  created_at: string | null;
}

export interface MessageHistoryPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface MessageHistoryResponse {
  success: boolean;
  data: {
    items: MessageHistoryItem[];
    pagination: MessageHistoryPagination;
  };
}