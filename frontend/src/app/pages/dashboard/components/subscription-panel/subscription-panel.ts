import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MqttApiService } from '../../../../core/services/mqtt-api.service';
import { StatusResponse } from '../../../../core/models/mqtt.models';
import { getApiErrorMessage } from '../../../../core/utils/api-error.util';

import {
  DEFAULT_SUBSCRIBE_QOS,
  DEFAULT_SUBSCRIBE_TOPIC
} from '../../dashboard.config';

import {
  getSubscriptionQos,
  hasSameSubscriptionQos,
  isTopicSubscribed
} from '../../dashboard.helpers';

@Component({
  selector: 'app-subscription-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './subscription-panel.html',
  styleUrl: './subscription-panel.css'
})
export class SubscriptionPanel {
  @Input() topics: string[] = [];
  @Input() status: StatusResponse | null = null;

  @Output() subscriptionChanged = new EventEmitter<string>();
  @Output() activeTopicChanged = new EventEmitter<string>();

  subscribeTopic = DEFAULT_SUBSCRIBE_TOPIC;
  subscribeQos = DEFAULT_SUBSCRIBE_QOS;

  infoMessage = '';
  errorMessage = '';
  loading = false;

  constructor(private api: MqttApiService) {}

  subscribeToTopic(): void {
    this.clearNotifications();

    const topic = this.subscribeTopic.trim();
    const qos = Number(this.subscribeQos);

    if (!topic) {
      this.errorMessage = 'Topic is required.';
      return;
    }

    this.loading = true;

    this.api.subscribe({ topic, qos }).subscribe({
      next: () => {
        this.infoMessage = `Subscribed to ${topic}.`;
        this.activeTopicChanged.emit(topic);
        this.subscriptionChanged.emit(topic);
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'Subscribe failed.');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  unsubscribeFromTopic(): void {
    this.clearNotifications();

    const topic = this.subscribeTopic.trim();

    if (!topic) {
      this.errorMessage = 'Topic is required.';
      return;
    }

    this.loading = true;

    this.api.unsubscribe({ topic }).subscribe({
      next: () => {
        this.infoMessage = `Unsubscribed from ${topic}.`;
        this.subscriptionChanged.emit(topic);
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'Unsubscribe failed.');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  isSelectedTopicSubscribed(): boolean {
    return isTopicSubscribed(this.status?.subscriptions ?? {}, this.subscribeTopic);
  }

  isSelectedTopicSubscribedWithSameQos(): boolean {
    return hasSameSubscriptionQos(
      this.status?.subscriptions ?? {},
      this.subscribeTopic,
      Number(this.subscribeQos)
    );
  }

  getSelectedTopicQos(): number | null {
    return getSubscriptionQos(this.status?.subscriptions ?? {}, this.subscribeTopic);
  }

  private clearNotifications(): void {
    this.infoMessage = '';
    this.errorMessage = '';
  }
}