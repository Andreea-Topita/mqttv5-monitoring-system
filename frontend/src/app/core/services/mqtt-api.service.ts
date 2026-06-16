import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import {
  ActionResponse,
  ConnectRequest,
  DeviceConfigRequest,
  MessageHistoryResponse,
  MessageItem,
  PeriodicPublishRequest,
  PublishMessageRequest,
  StatusResponse,
  SubscribeRequest,
  UnsubscribeRequest
} from '../models/mqtt.models';

@Injectable({
  providedIn: 'root'
})
export class MqttApiService {
  private baseUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  connect(payload: ConnectRequest) {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/connection/connect`, payload);
  }

  disconnect() {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/connection/disconnect`, {});
  }

  getStatus() {
    return this.http.get<StatusResponse>(`${this.baseUrl}/api/connection/status`);
  }

  subscribe(payload: SubscribeRequest) {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/subscription/subscribe`, payload);
  }

  unsubscribe(payload: UnsubscribeRequest) {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/subscription/unsubscribe`, payload);
  }

  publishMessage(payload: PublishMessageRequest) {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/publishing/publish-message`, payload);
  }

  configureDevice(payload: DeviceConfigRequest) {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/publishing/device-config`, payload);
  }

  startPeriodic(payload: PeriodicPublishRequest) {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/publishing/start-periodic`, payload);
  }

  stopPeriodic() {
    return this.http.post<ActionResponse>(`${this.baseUrl}/api/publishing/stop-periodic`, {});
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

  getMessageHistory(
    topic?: string,
    direction?: 'INBOUND' | 'OUTBOUND',
    page: number = 1,
    pageSize: number = 20
  ) {
    let params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);

    if (topic) {
      params = params.set('topic', topic);
    }

    if (direction) {
      params = params.set('direction', direction);
    }

    return this.http.get<MessageHistoryResponse>(
      `${this.baseUrl}/api/messages/history`,
      { params }
    );
  }
}