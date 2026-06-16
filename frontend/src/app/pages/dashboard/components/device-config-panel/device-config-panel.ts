import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  DeviceStatus,
  StatusResponse
} from '../../../../core/models/mqtt.models';

import { MqttApiService } from '../../../../core/services/mqtt-api.service';
import { getApiErrorMessage } from '../../../../core/utils/api-error.util';

@Component({
  selector: 'app-device-config-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './device-config-panel.html',
  styleUrl: './device-config-panel.css'
})
export class DeviceConfigPanel implements OnChanges {
  @Input() devices: DeviceStatus[] = [];
  @Input() status: StatusResponse | null = null;

  @Output() configSent = new EventEmitter<void>();

  selectedClientId = '';
  publishQos = 1;
  publishInterval = 3;
  messageQos = 0;

  infoMessage = '';
  errorMessage = '';
  loading = false;

  constructor(private api: MqttApiService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['devices']) {
      return;
    }

    if (
      this.selectedClientId &&
      this.devices.some((device) => device.client_id === this.selectedClientId)
    ) {
      return;
    }

    const firstOnlineDevice = this.devices.find((device) => device.status === 'online');
    const firstDevice = firstOnlineDevice ?? this.devices[0];

    this.selectedClientId = firstDevice?.client_id ?? '';
  }

  get selectedDevice(): DeviceStatus | null {
    return this.devices.find((device) => device.client_id === this.selectedClientId) ?? null;
  }

  get hasDevices(): boolean {
    return this.devices.length > 0;
  }

  get isSelectedDeviceOffline(): boolean {
    return this.selectedDevice?.status !== 'online';
  }

  configureSelectedDevice(): void {
    this.clearNotifications();

    if (!this.selectedClientId) {
      this.errorMessage = 'Select a detected device first.';
      return;
    }

    if (!this.publishInterval || this.publishInterval < 1) {
      this.errorMessage = 'Publish interval must be at least 1 second.';
      return;
    }

    this.loading = true;

    this.api.configureDevice({
        client_id: this.selectedClientId,
        publish_qos: Number(this.publishQos),
        publish_interval: Number(this.publishInterval),
        message_qos: 0
    }).subscribe({
      next: () => {
        this.infoMessage = `Configuration sent to ${this.selectedClientId}.`;
        this.configSent.emit();
      },
      error: (err) => {
        this.errorMessage = getApiErrorMessage(err, 'Device configuration failed.');
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