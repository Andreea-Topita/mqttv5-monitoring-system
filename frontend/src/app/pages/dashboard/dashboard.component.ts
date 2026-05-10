import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  ApiService,
  MessageItem,
  StatusResponse
} from '../../services/api.service';

import {
  DASHBOARD_TOPICS,
  DEFAULT_PERIODIC_INTERVAL,
  DEFAULT_PUBLISH_MESSAGE,
  DEFAULT_PUBLISH_QOS,
  DEFAULT_PUBLISH_TOPIC,
  DEFAULT_SUBSCRIBE_QOS,
  DEFAULT_SUBSCRIBE_TOPIC,
  PERIODIC_STATUS_REFRESH_DELAY_MS,
  POLLING_INTERVAL_MS,
  STATUS_REFRESH_DELAY_MS,
  STATUS_SYNC_PAUSE_MS
} from './dashboard.config';

import {
  LatestTelemetryState,
  createInitialStatus,
  createInitialTelemetryState,
  getNextActiveTopic,
  getSubscriptionQos,
  hasSameSubscriptionQos,
  isTopicSubscribed,
  normalizeStatus,
  updateTelemetryState
} from './dashboard.helpers';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit, OnDestroy {
  topics = DASHBOARD_TOPICS;

  status: StatusResponse = createInitialStatus();

  publishTopic = DEFAULT_PUBLISH_TOPIC;
  publishMessage = DEFAULT_PUBLISH_MESSAGE;
  publishQos = DEFAULT_PUBLISH_QOS;
  periodicInterval = DEFAULT_PERIODIC_INTERVAL;

  subscribeTopic = DEFAULT_SUBSCRIBE_TOPIC;
  subscribeQos = DEFAULT_SUBSCRIBE_QOS;

  activeMessageTopic = '';
  messages: MessageItem[] = [];
  lastMessageId = 0;

  latestStatus = '-';
  latestTemperature = '-';
  latestHumidity = '-';

  infoMessage = '';
  errorMessage = '';

  private pollingId: number | null = null;
  private loadingStatus = false;
  private loadingMessages = false;
  private pauseStatusSyncUntil = 0;
  private destroyed = false;

  constructor(
    private api: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadStatus();
    this.loadMessages();
    this.startPolling();
  }

  ngOnDestroy() {
    this.destroyed = true;
    this.stopPolling();
  }

  private syncView() {
    if (!this.destroyed) {
      this.cdr.detectChanges();
    }
  }

  private stopPolling() {
    if (this.pollingId !== null) {
      clearInterval(this.pollingId);
      this.pollingId = null;
    }
  }

  private pauseStatusSync(ms: number) {
    this.pauseStatusSyncUntil = Date.now() + ms;
  }

  private refreshStatusAfterDelay(delayMs: number) {
    window.setTimeout(() => {
      this.loadStatus();
    }, delayMs);
  }

  private syncActiveTopicWithSubscriptions() {
    this.activeMessageTopic = getNextActiveTopic(
      this.status.subscriptions,
      this.subscribeTopic,
      this.activeMessageTopic
    );
  }

  private applyTelemetryState(nextTelemetry: LatestTelemetryState) {
    this.latestStatus = nextTelemetry.latestStatus;
    this.latestTemperature = nextTelemetry.latestTemperature;
    this.latestHumidity = nextTelemetry.latestHumidity;
  }

  private resetMessagesState() {
    this.messages = [];
    this.lastMessageId = 0;
  }

  private resetDashboardState() {
    this.status = createInitialStatus();
    this.activeMessageTopic = '';
    this.resetMessagesState();

    const telemetry = createInitialTelemetryState();
    this.applyTelemetryState(telemetry);
  }

  startPolling() {
    this.stopPolling();

    this.pollingId = window.setInterval(() => {
      this.loadStatus();
      this.loadMessages();
    }, POLLING_INTERVAL_MS);
  }

  loadStatus() {
    if (this.loadingStatus) {
      return;
    }

    this.loadingStatus = true;

    this.api.getStatus().subscribe({
      next: (res: StatusResponse) => {
        if (Date.now() < this.pauseStatusSyncUntil) {
          return;
        }

        this.status = normalizeStatus(res);
        this.syncActiveTopicWithSubscriptions();
        this.syncView();
      },
      error: () => {},
      complete: () => {
        this.loadingStatus = false;
        this.syncView();
      }
    });
  }

  loadMessages() {
    if (this.loadingMessages) {
      return;
    }

    this.loadingMessages = true;

    this.api.getMessages(undefined, this.lastMessageId).subscribe({
      next: (res: { success: boolean; messages: MessageItem[] }) => {
        if (res.messages.length > 0) {
          this.messages = [...this.messages, ...res.messages];
          this.lastMessageId = res.messages[res.messages.length - 1].id;

          const nextTelemetry = updateTelemetryState(
            {
              latestStatus: this.latestStatus,
              latestTemperature: this.latestTemperature,
              latestHumidity: this.latestHumidity
            },
            res.messages
          );

          this.applyTelemetryState(nextTelemetry);
          this.syncView();
        }
      },
      error: () => {},
      complete: () => {
        this.loadingMessages = false;
        this.syncView();
      }
    });
  }

  disconnect() {
    this.stopPolling();
    this.clearNotifications();

    this.api.disconnect().subscribe({
      next: () => {
        this.resetDashboardState();
        this.syncView();
        this.router.navigate(['/connect']);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Disconnect failed.';
        this.syncView();
      }
    });
  }

  publishMessageNow() {
    this.clearNotifications();

    this.api.publishMessage({
      topic: this.publishTopic,
      message: this.publishMessage,
      qos: this.publishQos
    }).subscribe({
      next: () => {
        this.infoMessage = `Message published to ${this.publishTopic}.`;
        this.syncView();
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Publish failed.';
        this.syncView();
      }
    });
  }

  startPeriodicPublishing() {
    this.clearNotifications();

    this.api.startPeriodic({
      topic: this.publishTopic,
      message: this.publishMessage,
      qos: this.publishQos,
      interval: this.periodicInterval
    }).subscribe({
      next: () => {
        this.infoMessage = 'Periodic publishing started.';
        this.status = {
          ...this.status,
          periodic_publishing: true
        };
        this.syncView();
        this.refreshStatusAfterDelay(PERIODIC_STATUS_REFRESH_DELAY_MS);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Periodic publish failed.';
        this.syncView();
      }
    });
  }

  stopPeriodicPublishing() {
    this.clearNotifications();

    this.api.stopPeriodic().subscribe({
      next: () => {
        this.infoMessage = 'Periodic publishing stopped.';
        this.status = {
          ...this.status,
          periodic_publishing: false
        };
        this.syncView();
        this.refreshStatusAfterDelay(PERIODIC_STATUS_REFRESH_DELAY_MS);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Stop periodic failed.';
        this.syncView();
      }
    });
  }

  subscribeToTopic() {
    this.clearNotifications();
    this.stopPolling();

    const topic = this.subscribeTopic;
    const qos = Number(this.subscribeQos);

    this.api.subscribe({ topic, qos }).subscribe({
      next: () => {
        this.infoMessage = `Subscribed to ${topic}.`;
        this.pauseStatusSync(STATUS_SYNC_PAUSE_MS);

        this.status = {
          ...this.status,
          subscriptions: {
            ...this.status.subscriptions,
            [topic]: qos
          }
        };

        this.activeMessageTopic = topic;
        this.resetMessagesState();

        this.syncView();
        this.loadMessages();
        this.startPolling();
        this.refreshStatusAfterDelay(STATUS_REFRESH_DELAY_MS);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Subscribe failed.';
        this.startPolling();
        this.syncView();
      }
    });
  }

  unsubscribeFromTopic() {
    this.clearNotifications();
    this.stopPolling();

    const topic = this.subscribeTopic;

    this.api.unsubscribe({ topic }).subscribe({
      next: () => {
        this.infoMessage = `Unsubscribed from ${topic}.`;
        this.pauseStatusSync(STATUS_SYNC_PAUSE_MS);

        const updatedSubscriptions = { ...this.status.subscriptions };
        delete updatedSubscriptions[topic];

        this.status = {
          ...this.status,
          subscriptions: updatedSubscriptions
        };

        if (this.activeMessageTopic === topic) {
          this.activeMessageTopic = '';
        }

        this.resetMessagesState();
        this.syncActiveTopicWithSubscriptions();

        this.syncView();
        this.loadMessages();
        this.startPolling();
        this.refreshStatusAfterDelay(STATUS_REFRESH_DELAY_MS);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Unsubscribe failed.';
        this.startPolling();
        this.syncView();
      }
    });
  }

  get displayedMessages(): MessageItem[] {
    if (!this.activeMessageTopic) {
      return [];
    }

    return this.messages.filter(msg => msg.topic === this.activeMessageTopic);
  }

  clearNotifications() {
    this.infoMessage = '';
    this.errorMessage = '';
  }

  isSelectedTopicSubscribed(): boolean {
    return isTopicSubscribed(this.status.subscriptions, this.subscribeTopic);
  }

  isSelectedTopicSubscribedWithSameQos(): boolean {
    return hasSameSubscriptionQos(
      this.status.subscriptions,
      this.subscribeTopic,
      this.subscribeQos
    );
  }

  getSelectedTopicQos(): number | null {
    return getSubscriptionQos(this.status.subscriptions, this.subscribeTopic);
  }

  onSubscribeQosChange(value: any) {
    this.subscribeQos = Number(value);
    this.syncView();
  }
}