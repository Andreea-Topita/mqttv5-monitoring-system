import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  ApiService,
  MessageItem,
  StatusResponse
} from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit, OnDestroy {
  topics = [
    'licenta/pico/status',
    'licenta/pico/temperatura',
    'licenta/pico/umiditate',
    'licenta/pc/test',
    'licenta/pc/comenzi'
  ];

  status: StatusResponse = {
    connected: false,
    periodic_publishing: false,
    subscriptions: {}
  };

  publishTopic = 'licenta/pc/test';
  publishMessage = 'mesaj test de pe pc';
  publishQos = 0;
  periodicInterval = 5;

  subscribeTopic = 'licenta/pico/temperatura';
  subscribeQos = 0;

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

  constructor(
    private api: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadStatus();
    this.startPolling();
  }

  ngOnDestroy() {
    this.stopPolling();
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

  startPolling() {
    this.stopPolling();

    this.pollingId = window.setInterval(() => {
      this.loadStatus();

      if (this.status.connected) {
        this.loadMessages();
      }
    }, 2000);
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

        this.status = res;
      },
      error: () => {},
      complete: () => {
        this.loadingStatus = false;
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
          this.updateLatestValues(res.messages);
        }
      },
      error: () => {},
      complete: () => {
        this.loadingMessages = false;
      }
    });
  }

  updateLatestValues(newMessages: MessageItem[]) {
    for (const msg of newMessages) {
      if (msg.topic === 'licenta/pico/status') {
        this.latestStatus = msg.message;
      }

      if (msg.topic === 'licenta/pico/temperatura') {
        this.latestTemperature = msg.message;
      }

      if (msg.topic === 'licenta/pico/umiditate') {
        this.latestHumidity = msg.message;
      }
    }
  }

  disconnect() {
    this.stopPolling();

    this.api.disconnect().subscribe({
      next: () => {
        this.router.navigate(['/connect']);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Disconnect failed.';
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
        this.infoMessage = `Mesaj publicat pe topicul ${this.publishTopic}.`;
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Publish failed.';
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
        this.infoMessage = 'Periodic publish pornit.';
        setTimeout(() => this.loadStatus(), 300);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Periodic publish failed.';
      }
    });
  }

  stopPeriodicPublishing() {
    this.clearNotifications();

    this.api.stopPeriodic().subscribe({
      next: () => {
        this.infoMessage = 'Periodic publish oprit.';
        setTimeout(() => this.loadStatus(), 300);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Stop periodic failed.';
      }
    });
  }

  subscribeToTopic() {
    this.clearNotifications();
    this.stopPolling();

    this.api.subscribe({
      topic: this.subscribeTopic,
      qos: this.subscribeQos
    }).subscribe({
      next: () => {
        this.infoMessage = `Subscribed la ${this.subscribeTopic}.`;

        this.pauseStatusSync(1200);

        this.status = {
          ...this.status,
          subscriptions: {
            ...this.status.subscriptions,
            [this.subscribeTopic]: this.subscribeQos
          }
        };

        this.activeMessageTopic = this.subscribeTopic;
        this.messages = [];
        this.lastMessageId = 0;

        setTimeout(() => {
          this.loadMessages();
          this.startPolling();
        }, 300);

        setTimeout(() => {
          this.loadStatus();
        }, 1300);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Subscribe failed.';
        this.startPolling();
      }
    });
  }

  unsubscribeFromTopic() {
    this.clearNotifications();
    this.stopPolling();

    this.api.unsubscribe({
      topic: this.subscribeTopic
    }).subscribe({
      next: () => {
        this.infoMessage = `Unsubscribed de la ${this.subscribeTopic}.`;

        this.pauseStatusSync(1200);

        const updatedSubscriptions = { ...this.status.subscriptions };
        delete updatedSubscriptions[this.subscribeTopic];

        this.status = {
          ...this.status,
          subscriptions: updatedSubscriptions
        };

        if (this.activeMessageTopic === this.subscribeTopic) {
          this.activeMessageTopic = '';
        }

        this.messages = [];
        this.lastMessageId = 0;

        setTimeout(() => {
          this.startPolling();
        }, 300);

        setTimeout(() => {
          this.loadStatus();
        }, 1300);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Unsubscribe failed.';
        this.startPolling();
      }
    });
  }

  
  getSubscriptionStatus(): string {
    const qos = this.status.subscriptions[this.subscribeTopic];

    if (qos === undefined) {
      return 'UNSUBSCRIBED';
    }

    return `SUBSCRIBED (QoS ${qos})`;
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
}