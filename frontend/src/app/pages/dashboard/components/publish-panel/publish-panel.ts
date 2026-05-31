import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MqttApiService } from '../../../../core/services/mqtt-api.service';
import { StatusResponse } from '../../../../core/models/mqtt.models';
import { getApiErrorMessage } from '../../../../core/utils/api-error.util';

import {
  DEFAULT_PERIODIC_INTERVAL,
  DEFAULT_PUBLISH_MESSAGE,
  DEFAULT_PUBLISH_QOS,
  DEFAULT_PUBLISH_TOPIC
} from '../../dashboard.config';

@Component({
  selector: 'app-publish-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './publish-panel.html',
  styleUrl: './publish-panel.css'
})
export class PublishPanel {
  @Input() topics: string[] = [];
  @Input() status: StatusResponse | null = null;

  @Output() statusRefreshRequested = new EventEmitter<void>();

  publishTopic = DEFAULT_PUBLISH_TOPIC;
  publishMessage = DEFAULT_PUBLISH_MESSAGE;
  publishQos = DEFAULT_PUBLISH_QOS;
  periodicInterval = DEFAULT_PERIODIC_INTERVAL;

  infoMessage = '';
  errorMessage = '';
  loading = false;

  constructor(private api: MqttApiService) {}

  publishMessageNow(): void {
    this.clearNotifications();

    if (!this.publishTopic.trim() || !this.publishMessage.trim()) {
      this.errorMessage = 'Topic and message are required.';
      return;
    }

    this.loading = true;

    this.api.publishMessage({
      topic: this.publishTopic.trim(),
      message: this.publishMessage,
      qos: Number(this.publishQos)
    }).subscribe({
      next: () => {
        this.infoMessage = `Message published to ${this.publishTopic}.`;
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'Publish failed.');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  startPeriodicPublishing(): void {
    this.clearNotifications();

    if (!this.publishTopic.trim() || !this.publishMessage.trim()) {
      this.errorMessage = 'Topic and message are required.';
      return;
    }

    if (!this.periodicInterval || this.periodicInterval < 1) {
      this.errorMessage = 'Interval must be at least 1 second.';
      return;
    }

    this.loading = true;

    this.api.startPeriodic({
      topic: this.publishTopic.trim(),
      message: this.publishMessage,
      qos: Number(this.publishQos),
      interval: Number(this.periodicInterval)
    }).subscribe({
      next: () => {
        this.infoMessage = 'Periodic publishing started.';
        this.statusRefreshRequested.emit();
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'Periodic publish failed.');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  stopPeriodicPublishing(): void {
    this.clearNotifications();
    this.loading = true;

    this.api.stopPeriodic().subscribe({
      next: () => {
        this.infoMessage = 'Periodic publishing stopped.';
        this.statusRefreshRequested.emit();
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'Stop periodic failed.');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  private clearNotifications(): void {
    this.infoMessage = '';
    this.errorMessage = '';
  }
}