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
  topics = ['Cpu load', 'Memory usage', 'Disk usage'];

  status: StatusResponse = {
    connected: false,
    periodic_publishing: false,
    subscriptions: {}
  };

  publishTopic = 'Cpu load';
  publishQos = 0;
  periodicInterval = 5;

  subscribeTopic = 'Cpu load';
  subscribeQos = 0;

  activeMessageTopic = '';
  messages: MessageItem[] = [];
  lastMessageId = 0;

  infoMessage = '';
  errorMessage = '';

  private pollingId: number | null = null;

  constructor(
    private api: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadStatus();
    this.startPolling();
  }

  ngOnDestroy() {
    if (this.pollingId !== null) {
      clearInterval(this.pollingId);
    }
  }

  startPolling() {
    this.pollingId = window.setInterval(() => {
      this.loadStatus();

      if (this.activeMessageTopic) {
        this.loadMessages();
      }
    }, 2000);
  }

  loadStatus() {
    this.api.getStatus().subscribe({
      next: (res: StatusResponse) => {
        this.status = res;
      }
    });
  }

  disconnect() {
    this.api.disconnect().subscribe({
      next: () => {
        this.router.navigate(['/connect']);
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Disconnect failed.';
      }
    });
  }

  publishMetric() {
    this.clearMessages();

    this.api.publishMetric({
      topic: this.publishTopic,
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
    this.clearMessages();

    this.api.startPeriodic({
      topic: this.publishTopic,
      qos: this.publishQos,
      interval: this.periodicInterval
    }).subscribe({
      next: () => {
        this.infoMessage = 'Periodic publish pornit.';
        this.loadStatus();
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Periodic publish failed.';
      }
    });
  }

  stopPeriodicPublishing() {
    this.clearMessages();

    this.api.stopPeriodic().subscribe({
      next: () => {
        this.infoMessage = 'Periodic publish oprit.';
        this.loadStatus();
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Stop periodic failed.';
      }
    });
  }

  subscribeToTopic() {
    this.clearMessages();

    this.api.subscribe({
      topic: this.subscribeTopic,
      qos: this.subscribeQos
    }).subscribe({
      next: () => {
        this.infoMessage = `Subscribed la ${this.subscribeTopic}.`;
        this.activeMessageTopic = this.subscribeTopic;
        this.messages = [];
        this.lastMessageId = 0;
        this.loadStatus();
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Subscribe failed.';
      }
    });
  }

  unsubscribeFromTopic() {
    this.clearMessages();

    this.api.unsubscribe({
      topic: this.subscribeTopic
    }).subscribe({
      next: () => {
        this.infoMessage = `Unsubscribed de la ${this.subscribeTopic}.`;

        if (this.activeMessageTopic === this.subscribeTopic) {
          this.activeMessageTopic = '';
          this.messages = [];
          this.lastMessageId = 0;
        }

        this.loadStatus();
      },
      error: (err: any) => {
        this.errorMessage = err?.error?.detail || 'Unsubscribe failed.';
      }
    });
  }

  loadMessages() {
    this.api.getMessages(this.activeMessageTopic, this.lastMessageId).subscribe({
      next: (res: { success: boolean; messages: MessageItem[] }) => {
        if (res.messages.length > 0) {
          this.messages = [...this.messages, ...res.messages];
          this.lastMessageId = res.messages[res.messages.length - 1].id;
        }
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

  clearMessages() {
    this.infoMessage = '';
    this.errorMessage = '';
  }
}