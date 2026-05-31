import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-telemetry-overview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './telemetry-overview.html',
  styleUrl: './telemetry-overview.css'
})
export class TelemetryOverview {
  @Input() connected = false;
  @Input() periodicPublishing = false;

  @Input() latestStatus = '-';
  @Input() latestTemperature = '-';
  @Input() latestHumidity = '-';
}