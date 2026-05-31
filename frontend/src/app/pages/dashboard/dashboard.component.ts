import {
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { MqttApiService } from '../../core/services/mqtt-api.service';

import {
  MessageItem,
  StatusResponse
} from '../../core/models/mqtt.models';

import {
  DASHBOARD_TOPICS,
  POLLING_INTERVAL_MS 
} from './dashboard.config';

import {
  LatestTelemetryState,
  createInitialStatus,
  createInitialTelemetryState,
  normalizeStatus,
  updateTelemetryState
} from './dashboard.helpers';

import { DashboardHeader } from './components/dashboard-header/dashboard-header';
import { TelemetryOverview } from './components/telemetry-overview/telemetry-overview';
import { PublishPanel } from './components/publish-panel/publish-panel';
import { SubscriptionPanel } from './components/subscription-panel/subscription-panel';
import { LiveMessagesPanel } from './components/live-messages-panel/live-messages-panel';
import { MessageHistoryPanel } from './components/message-history-panel/message-history-panel';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    DashboardHeader,
    TelemetryOverview,
    PublishPanel,
    SubscriptionPanel,
    LiveMessagesPanel,
    MessageHistoryPanel
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit, OnDestroy {
  topics = DASHBOARD_TOPICS;

  status: StatusResponse = createInitialStatus();

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
  private destroyed = false;

  constructor(
    private api: MqttApiService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadStatus();
    this.loadMessages();
    this.startPolling();
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.stopPolling();
  }

  get displayedMessages(): MessageItem[] {
    if (!this.activeMessageTopic) {
      return [];
    }

    return this.messages
      .filter((msg) => msg.topic === this.activeMessageTopic)
      .slice(-20);
  }

  loadStatus(): void {
    if (this.loadingStatus) {
      return;
    }

    this.loadingStatus = true;

    this.api.getStatus().subscribe({
      next: (res: StatusResponse) => {
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

  loadMessages(): void {
    if (this.loadingMessages) {
      return;
    }

    this.loadingMessages = true;

    this.api.getMessages(undefined, this.lastMessageId).subscribe({
      next: (res: { success: boolean; messages: MessageItem[] }) => {
        if (res.messages.length > 0) {
          this.messages = [...this.messages, ...res.messages].slice(-100);
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

  clearLiveMessages(): void {
    this.messages = [];
    this.lastMessageId = 0;
    this.syncView();
  }

  setActiveMessageTopic(topic: string): void {
    this.activeMessageTopic = topic;
    this.syncView();
  }

  handleSubscriptionChanged(topic: string): void {
    if (topic) {
      this.activeMessageTopic = topic;
    }

    this.clearLiveMessages();
    this.loadStatus();
    this.loadMessages();
  }

  handleStatusRefreshRequested(): void {
    this.loadStatus();
  }

  disconnect(): void {
    this.stopPolling();
    this.clearNotifications();

    this.api.disconnect().subscribe({
      next: () => {
        this.resetDashboardState();
        this.router.navigate(['/connect']);
      },
      error: () => {
        this.errorMessage = 'Disconnect failed.';
        this.syncView();
      }
    });
  }

  logout(): void {
    this.stopPolling();

    this.api.disconnect().subscribe({
      next: () => {
        this.finishLogout();
      },
      error: () => {
        this.finishLogout();
      }
    });
  }

  goToCharts(): void {
    this.router.navigate(['/charts']);
  }

  private finishLogout(): void {
    this.authService.logout();
    this.resetDashboardState();
    this.router.navigate(['/login']);
  }

  private startPolling(): void {
    this.stopPolling();

    this.pollingId = window.setInterval(() => {
      this.loadStatus();
      this.loadMessages();
    }, POLLING_INTERVAL_MS);
  }

  private stopPolling(): void {
    if (this.pollingId !== null) {
      clearInterval(this.pollingId);
      this.pollingId = null;
    }
  }

  private syncActiveTopicWithSubscriptions(): void {
    const subscriptions = this.status.subscriptions ?? {};
    const subscribedTopics = Object.keys(subscriptions);

    if (
      this.activeMessageTopic &&
      subscriptions[this.activeMessageTopic] !== undefined
    ) {
      return;
    }

    this.activeMessageTopic = subscribedTopics.length > 0 ? subscribedTopics[0] : '';
  }

  private applyTelemetryState(nextTelemetry: LatestTelemetryState): void {
    this.latestStatus = nextTelemetry.latestStatus;
    this.latestTemperature = nextTelemetry.latestTemperature;
    this.latestHumidity = nextTelemetry.latestHumidity;
  }

  private resetDashboardState(): void {
    this.status = createInitialStatus();
    this.activeMessageTopic = '';
    this.messages = [];
    this.lastMessageId = 0;

    const telemetry = createInitialTelemetryState();
    this.applyTelemetryState(telemetry);

    this.clearNotifications();
    this.syncView();
  }

  private clearNotifications(): void {
    this.infoMessage = '';
    this.errorMessage = '';
  }

  private syncView(): void {
    if (!this.destroyed) {
      this.cdr.detectChanges();
    }
  }
}