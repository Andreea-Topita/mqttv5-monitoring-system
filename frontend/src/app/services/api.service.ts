import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

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
}

export interface SubscribeRequest {
  topic: string;
  qos: number;
}

export interface UnsubscribeRequest {
  topic: string;
}

export interface PublishMetricRequest {
  topic: string;
  qos: number;
}

export interface PeriodicPublishRequest {
  topic: string;
  qos: number;
  interval: number;
}

export interface MessageItem {
  id: number;
  topic: string;
  message: string;
  timestamp: number;
}

export interface StatusResponse {
  connected: boolean;
  periodic_publishing: boolean;
  subscriptions: Record<string, number>;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  connect(payload: ConnectRequest) {
    return this.http.post(`${this.baseUrl}/api/connection/connect`, payload);
  }

  disconnect() {
    return this.http.post(`${this.baseUrl}/api/connection/disconnect`, {});
  }

  getStatus() {
    return this.http.get<StatusResponse>(`${this.baseUrl}/api/connection/status`);
  }

  subscribe(payload: SubscribeRequest) {
    return this.http.post(`${this.baseUrl}/api/subscription/subscribe`, payload);
  }

  unsubscribe(payload: UnsubscribeRequest) {
    return this.http.post(`${this.baseUrl}/api/subscription/unsubscribe`, payload);
  }

  publishMetric(payload: PublishMetricRequest) {
    return this.http.post(`${this.baseUrl}/api/publishing/publish-metric`, payload);
  }

  startPeriodic(payload: PeriodicPublishRequest) {
    return this.http.post(`${this.baseUrl}/api/publishing/start-periodic`, payload);
  }

  stopPeriodic() {
    return this.http.post(`${this.baseUrl}/api/publishing/stop-periodic`, {});
  }

  getMessages(topic?: string, afterId?: number) {
    let params = new HttpParams();

    if (topic) {
      params = params.set('topic', topic);
    }

    if (afterId !== undefined) {
      params = params.set('after_id', afterId);
    }

    return this.http.get<{ success: boolean; messages: MessageItem[] }>(
      `${this.baseUrl}/api/messages`,
      { params }
    );
  }
}