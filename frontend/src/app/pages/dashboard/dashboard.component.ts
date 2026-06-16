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
  DeviceTelemetryMap,
  buildDashboardTopics,
  createInitialDeviceTelemetryState,
  createInitialStatus,
  getNextActiveTopic,
  normalizeStatus,
  syncTelemetryWithDevices,
  topicMatchesFilter,
  updateDeviceTelemetryState
} from './dashboard.helpers';

import { DashboardHeader } from './components/dashboard-header/dashboard-header';
import { TelemetryOverview } from './components/telemetry-overview/telemetry-overview';
import { DeviceConfigPanel } from './components/device-config-panel/device-config-panel';
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
    DeviceConfigPanel,
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
  deviceTelemetry: DeviceTelemetryMap = createInitialDeviceTelemetryState();

  activeMessageTopic = '';
  messages: MessageItem[] = [];
  lastMessageId = 0;

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
      .filter((msg) => topicMatchesFilter(this.activeMessageTopic, msg.topic))
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
        this.deviceTelemetry = syncTelemetryWithDevices(
          this.deviceTelemetry,
          this.status.devices
        );

        this.refreshTopicOptions();
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
          this.messages = [...this.messages, ...res.messages].slice(-120);
          this.lastMessageId = res.messages[res.messages.length - 1].id;

          this.deviceTelemetry = updateDeviceTelemetryState(
            this.deviceTelemetry,
            res.messages
          );

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

  handleDeviceConfigSent(): void {
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

  private refreshTopicOptions(): void {
    this.topics = buildDashboardTopics(this.status.devices, DASHBOARD_TOPICS);
    this.activeMessageTopic = getNextActiveTopic(this.activeMessageTopic, this.topics);
  }

  private resetDashboardState(): void {
    this.status = createInitialStatus();
    this.deviceTelemetry = createInitialDeviceTelemetryState();

    this.activeMessageTopic = '';
    this.messages = [];
    this.lastMessageId = 0;
    this.topics = DASHBOARD_TOPICS;

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