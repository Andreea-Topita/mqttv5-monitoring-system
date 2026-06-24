import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { formatMqttPayload } from '../../../../core/utils/mqtt-message-display.util';

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
  @Input() topics: string[] = [];
  @Input() activeMessageTopic = '';
  @Input() displayedMessages: MessageItem[] = [];

  @Output() activeMessageTopicChange = new EventEmitter<string>();
  @Output() clearMessagesClicked = new EventEmitter<void>();

  get liveTopicOptions(): string[] {
    const availableTopics = this.topics.filter(
      (topic) => !topic.endsWith('/config')
    );

    if (
      this.activeMessageTopic &&
      !this.activeMessageTopic.endsWith('/config') &&
      !availableTopics.includes(this.activeMessageTopic)
    ) {
      return [...availableTopics, this.activeMessageTopic];
    }

    return availableTopics;
  }
  
  setActiveTopic(topic: string): void {
    this.activeMessageTopicChange.emit(topic);
  }

  formatMessage(msg: MessageItem) {
    return formatMqttPayload(msg.topic, msg.message, msg.timestamp);
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