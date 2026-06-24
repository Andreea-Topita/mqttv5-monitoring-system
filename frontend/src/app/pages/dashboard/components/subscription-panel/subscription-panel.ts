import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MqttApiService } from '../../../../core/services/mqtt-api.service';
import { StatusResponse } from '../../../../core/models/mqtt.models';
import { getApiErrorMessage } from '../../../../core/utils/api-error.util';

import {
  AUTOMATIC_SUBSCRIPTION_FILTERS,
  DEFAULT_SUBSCRIBE_QOS,
  DEFAULT_SUBSCRIBE_TOPIC
} from '../../dashboard.config';

import {
  getSubscriptionQos,
  hasSameSubscriptionQos,
  isTopicSubscribed,
  topicMatchesFilter
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

    if (this.isSelectedTopicManagedAutomatically()) {
      this.infoMessage =
        'This subscription is managed automatically by the application.';
      return;
    }

    const coveringSubscription = this.getCoveringWildcardSubscription();

    // verificare suplimentara chiar daca butonul este dezactivat in interfata
    if (!this.isSelectedTopicSubscribed() && coveringSubscription) {
      this.infoMessage =
        `This topic is already included through ${coveringSubscription.filter} ` +
        `with QoS ${coveringSubscription.qos}.`;
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

    if (this.isSelectedTopicManagedAutomatically()) {
      this.infoMessage =
        'This subscription is managed automatically and cannot be removed here.';
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
    const topic = this.subscribeTopic.trim();

    return isTopicSubscribed(
      this.status?.subscriptions ?? {},
      topic
    );
  }

  isSelectedTopicSubscribedWithSameQos(): boolean {
    const topic = this.subscribeTopic.trim();

    return hasSameSubscriptionQos(
      this.status?.subscriptions ?? {},
      topic,
      Number(this.subscribeQos)
    );
  }

  getSelectedTopicQos(): number | null {
    const topic = this.subscribeTopic.trim();

    return getSubscriptionQos(
      this.status?.subscriptions ?? {},
      topic
    );
  }

  getCoveringWildcardSubscription(): {
    filter: string;
    qos: number;
  } | null {
    const topic = this.subscribeTopic.trim();

    if (!topic) {
      return null;
    }

    // daca topicul selectat este chiar un filtru wildcard
    // verificarea lui se face ca abonare directa
    if (topic.includes('+') || topic.includes('#')) {
      return null;
    }

    const subscriptions = this.status?.subscriptions ?? {};

    for (const [filter, qos] of Object.entries(subscriptions)) {
      // abonarea exacta este verificata separat
      if (filter === topic) {
        continue;
      }

      // sunt verificate doar filtrele wildcard
      if (!filter.includes('+') && !filter.includes('#')) {
        continue;
      }

      if (topicMatchesFilter(filter, topic)) {
        return {
          filter,
          qos: Number(qos)
        };
      }
    }

    return null;
  }

  isSelectedTopicCoveredByWildcard(): boolean {
    return this.getCoveringWildcardSubscription() !== null;
  }

  isSelectedTopicManagedAutomatically(): boolean {
    const topic = this.subscribeTopic.trim();

    return AUTOMATIC_SUBSCRIPTION_FILTERS.includes(topic);
  }

  onSelectionChanged(): void {
    this.clearNotifications();
  }

  private clearNotifications(): void {
    this.infoMessage = '';
    this.errorMessage = '';
  }
}