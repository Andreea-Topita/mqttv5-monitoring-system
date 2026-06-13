import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MqttApiService } from '../../../../core/services/mqtt-api.service';
import { MessageHistoryItem } from '../../../../core/models/mqtt.models';
import { getApiErrorMessage } from '../../../../core/utils/api-error.util';

import { DEFAULT_HISTORY_PAGE_SIZE } from '../../dashboard.config';
import { formatMqttPayload } from '../../../../core/utils/mqtt-message-display.util';

@Component({
  selector: 'app-message-history-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './message-history-panel.html',
  styleUrl: './message-history-panel.css'
})
export class MessageHistoryPanel implements OnInit {
  @Input() topics: string[] = [];
  
  historyTopic = '';
  historyDirection: 'INBOUND' | 'OUTBOUND' | '' = '';
  historyPage = 1;
  historyPageSize = DEFAULT_HISTORY_PAGE_SIZE;

  historyItems: MessageHistoryItem[] = [];
  historyTotalPages = 0;
  historyTotalItems = 0;
  historyHasNext = false;
  historyHasPrevious = false;

  loading = false;
  errorMessage = '';
  expandedRawPayloadIds = new Set<number>();

  constructor(private api: MqttApiService) {}

  ngOnInit(): void {
    this.loadMessageHistory();
  }

  loadMessageHistory(): void {
    if (this.loading) {
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    this.api.getMessageHistory(
      this.historyTopic || undefined,
      this.historyDirection || undefined,
      this.historyPage,
      this.historyPageSize
    ).subscribe({
      next: (res) => {
        this.historyItems = res.data.items;
        this.expandedRawPayloadIds.clear();

        this.historyTotalPages = res.data.pagination.total_pages;
        this.historyTotalItems = res.data.pagination.total_items;
        this.historyHasNext = res.data.pagination.has_next;
        this.historyHasPrevious = res.data.pagination.has_previous;
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'History loading failed.');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  applyHistoryFilters(): void {
    this.historyPage = 1;
    this.loadMessageHistory();
  }

  resetHistoryFilters(): void {
    this.historyTopic = '';
    this.historyDirection = '';
    this.historyPage = 1;
    this.loadMessageHistory();
  }

  goToPreviousHistoryPage(): void {
    if (!this.historyHasPrevious) {
      return;
    }

    this.historyPage--;
    this.loadMessageHistory();
  }

  goToNextHistoryPage(): void {
    if (!this.historyHasNext) {
      return;
    }

    this.historyPage++;
    this.loadMessageHistory();
  }
  formatHistoryMessage(item: MessageHistoryItem) {
  return formatMqttPayload(
    item.topic,
    item.payload,
    this.getCreatedAtTimestamp(item.created_at)
  );
}

  toggleRawPayload(itemId: number): void {
    if (this.expandedRawPayloadIds.has(itemId)) {
      this.expandedRawPayloadIds.delete(itemId);
      return;
    }

    this.expandedRawPayloadIds.add(itemId);
  }

  isRawPayloadVisible(itemId: number): boolean {
    return this.expandedRawPayloadIds.has(itemId);
  }

  shouldShowRawPayloadButton(item: MessageHistoryItem): boolean {
    const formatted = this.formatHistoryMessage(item);

    return (
      formatted.isFormatted &&
      formatted.rawPayload.trim() !== formatted.valueText.trim()
    );
  }

  private getCreatedAtTimestamp(createdAt: string | null): number | undefined {
    if (!createdAt) {
      return undefined;
    }

    const milliseconds = Date.parse(createdAt);

    if (Number.isNaN(milliseconds)) {
      return undefined;
    }

    return milliseconds;
  }
}