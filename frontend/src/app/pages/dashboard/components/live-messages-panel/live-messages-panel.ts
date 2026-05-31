import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  MessageItem,
  StatusResponse
} from '../../../../core/models/mqtt.models';

@Component({
  selector: 'app-live-messages-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './live-messages-panel.html',
  styleUrl: './live-messages-panel.css'
})
export class LiveMessagesPanel {
  @Input() status: StatusResponse | null = null;
  @Input() activeMessageTopic = '';
  @Input() displayedMessages: MessageItem[] = [];

  @Output() activeMessageTopicChange = new EventEmitter<string>();
  @Output() clearMessagesClicked = new EventEmitter<void>();

  get subscribedTopics(): string[] {
    return Object.keys(this.status?.subscriptions ?? {});
  }

  setActiveTopic(topic: string): void {
    this.activeMessageTopicChange.emit(topic);
  }

  formatTimestamp(timestamp: number): string {
    if (!timestamp) {
      return '-';
    }

    const value = Number(timestamp);
    const milliseconds = value > 1000000000000 ? value : value * 1000;

    return new Date(milliseconds).toLocaleTimeString();
  }
}