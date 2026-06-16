import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DeviceStatus } from '../../../../core/models/mqtt.models';
import {
  DeviceLatestTelemetry,
  DeviceTelemetryMap
} from '../../dashboard.helpers';

@Component({
  selector: 'app-telemetry-overview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './telemetry-overview.html',
  styleUrl: './telemetry-overview.css'
})
export class TelemetryOverview {
  @Input() devices: DeviceStatus[] = [];
  @Input() telemetryByDevice: DeviceTelemetryMap = {};

  getTelemetry(device: DeviceStatus): DeviceLatestTelemetry {
    return this.telemetryByDevice[device.client_id] ?? {
      status: device.status || '-',
      temperature: '-',
      humidity: '-',
      lastSeenText: '-'
    };
  }

  getStatusLabel(device: DeviceStatus): string {
    return device.status || 'unknown';
  }
}