import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin, finalize, Subscription, timeout } from 'rxjs';

import { SensorMeasurementApiService } from '../../core/services/sensor-measurement.api.service';
import { SensorMeasurementItem } from '../../core/models/sensor-measurement.models';
import { getApiErrorMessage } from '../../core/utils/api-error.util';

interface SvgPoint {
  x: number;
  y: number;
  value: number;
  label: string;
}

interface AxisLabel {
  x: number;
  label: string;
}

interface YTick {
  y: number;
  label: string;
}

interface SensorChartData {
  title: string;
  description: string;
  topic: string;
  unit: string;
  items: SensorMeasurementItem[];
  points: SvgPoint[];
  polylinePoints: string;
  yTicks: YTick[];
  xLabels: AxisLabel[];
  latestValue: number | null;
  latestTime: string;
  minValue: number | null;
  maxValue: number | null;
  averageValue: number | null;
}

@Component({
  selector: 'app-charts',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './charts.component.html',
  styleUrl: './charts.component.css'
})
export class ChartsComponent implements OnInit, OnDestroy {
  readonly temperatureMeasurementName = 'temperature';
  readonly humidityMeasurementName = 'humidity';

  readonly temperatureTopicLabel = 'licenta/pico/temperatura';
  readonly humidityTopicLabel = 'licenta/pico/umiditate';

  readonly chartWidth = 1000;
  readonly chartHeight = 300;

  limit = 50;
  autoRefresh = false;
  refreshSeconds = 5;

  loading = false;
  errorMessage = '';
  infoMessage = '';

  charts: SensorChartData[] = [];

  private autoRefreshTimer: any = null;
  private chartsRequest: Subscription | null = null;
  private requestVersion = 0;

  constructor(
    private sensorApi: SensorMeasurementApiService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadCharts();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();

    if (this.chartsRequest) {
      this.chartsRequest.unsubscribe();
      this.chartsRequest = null;
    }
  }

  loadCharts(): void {
    this.requestVersion++;
    const currentRequest = this.requestVersion;

    if (this.chartsRequest) {
      this.chartsRequest.unsubscribe();
      this.chartsRequest = null;
    }

    this.loading = true;
    this.errorMessage = '';
    this.infoMessage = '';

    this.chartsRequest = forkJoin({
      temperature: this.sensorApi.getMeasurements(
        this.temperatureMeasurementName,
        undefined,
        undefined,
        Number(this.limit)
      ),
      humidity: this.sensorApi.getMeasurements(
        this.humidityMeasurementName,
        undefined,
        undefined,
        Number(this.limit)
      )
    })
      .pipe(
        timeout(10000),
        finalize(() => {
          if (currentRequest === this.requestVersion) {
            this.loading = false;
          }
        })
      )
      .subscribe({
        next: (res) => {
          const temperatureChart = this.buildChart(
            'Temperature',
            'Values received from the Pico temperature topic and stored in MySQL.',
            this.temperatureTopicLabel,
            res.temperature.data
          );

          const humidityChart = this.buildChart(
            'Humidity',
            'Values received from the Pico humidity topic and stored in MySQL.',
            this.humidityTopicLabel,
            res.humidity.data
          );

          this.charts = [temperatureChart, humidityChart];

          const totalItems =
            res.temperature.data.length + res.humidity.data.length;

          if (totalItems === 0) {
            this.infoMessage = 'No sensor measurements found in database.';
          } else {
            this.infoMessage = 'Charts loaded from database.';
          }
        },
        error: (err) => {
          this.errorMessage = getApiErrorMessage(
            err,
            'Could not load sensor measurements.'
          );
        }
      });
  }

  onAutoRefreshChanged(): void {
    if (this.autoRefresh) {
      this.startAutoRefresh();
      this.loadCharts();
      return;
    }

    this.stopAutoRefresh();
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  formatValue(value: number | null, unit: string): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '-';
    }

    return `${value.toFixed(2)} ${unit}`;
  }

  private startAutoRefresh(): void {
    this.stopAutoRefresh();

    const intervalMs = Math.max(2, Number(this.refreshSeconds)) * 1000;

    this.autoRefreshTimer = setInterval(() => {
      this.loadCharts();
    }, intervalMs);
  }

  private stopAutoRefresh(): void {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
      this.autoRefreshTimer = null;
    }
  }

  private buildChart(
    title: string,
    description: string,
    topic: string,
    rawItems: SensorMeasurementItem[]
  ): SensorChartData {
    const items = [...rawItems]
      .filter((item) => Number.isFinite(Number(item.numeric_value)))
      .sort((a, b) => {
        return new Date(a.measured_at).getTime() - new Date(b.measured_at).getTime();
      });

    const values = items.map((item) => Number(item.numeric_value));
    const unit = items.length > 0 ? items[items.length - 1].unit : '';

    const latestItem = items.length > 0 ? items[items.length - 1] : null;

    const minValue = values.length > 0 ? Math.min(...values) : null;
    const maxValue = values.length > 0 ? Math.max(...values) : null;
    const averageValue =
      values.length > 0
        ? values.reduce((sum, value) => sum + value, 0) / values.length
        : null;

    const points = this.createSvgPoints(items);
    const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(' ');

    return {
      title,
      description,
      topic,
      unit,
      items,
      points,
      polylinePoints,
      yTicks: this.createYTicks(values),
      xLabels: this.createXLabels(items),
      latestValue: latestItem ? Number(latestItem.numeric_value) : null,
      latestTime: latestItem ? this.formatDateTime(latestItem.measured_at) : '-',
      minValue,
      maxValue,
      averageValue
    };
  }

  private createSvgPoints(items: SensorMeasurementItem[]): SvgPoint[] {
    if (items.length === 0) {
      return [];
    }

    const values = items.map((item) => Number(item.numeric_value));
    const { min, max } = this.getValueRange(values);

    const paddingLeft = 62;
    const paddingRight = 28;
    const paddingTop = 26;
    const paddingBottom = 48;

    const plotWidth = this.chartWidth - paddingLeft - paddingRight;
    const plotHeight = this.chartHeight - paddingTop - paddingBottom;

    return items.map((item, index) => {
      const value = Number(item.numeric_value);

      const x =
        items.length === 1
          ? paddingLeft + plotWidth / 2
          : paddingLeft + (index / (items.length - 1)) * plotWidth;

      const y = paddingTop + ((max - value) / (max - min)) * plotHeight;

      return {
        x,
        y,
        value,
        label: this.formatDateTime(item.measured_at)
      };
    });
  }

  private createYTicks(values: number[]): YTick[] {
    if (values.length === 0) {
      return [];
    }

    const { min, max } = this.getValueRange(values);

    const paddingTop = 26;
    const paddingBottom = 48;
    const plotHeight = this.chartHeight - paddingTop - paddingBottom;

    const ticksCount = 5;
    const ticks: YTick[] = [];

    for (let i = 0; i < ticksCount; i++) {
      const ratio = i / (ticksCount - 1);
      const value = max - ratio * (max - min);
      const y = paddingTop + ratio * plotHeight;

      ticks.push({
        y,
        label: value.toFixed(1)
      });
    }

    return ticks;
  }

  private createXLabels(items: SensorMeasurementItem[]): AxisLabel[] {
    if (items.length === 0) {
      return [];
    }

    const paddingLeft = 62;
    const paddingRight = 28;
    const plotWidth = this.chartWidth - paddingLeft - paddingRight;

    const wantedLabels = Math.min(5, items.length);
    const labels: AxisLabel[] = [];

    for (let i = 0; i < wantedLabels; i++) {
      const index =
        wantedLabels === 1
          ? 0
          : Math.round((i / (wantedLabels - 1)) * (items.length - 1));

      const x =
        items.length === 1
          ? paddingLeft + plotWidth / 2
          : paddingLeft + (index / (items.length - 1)) * plotWidth;

      labels.push({
        x,
        label: this.formatTime(items[index].measured_at)
      });
    }

    return labels;
  }

  private getValueRange(values: number[]): { min: number; max: number } {
    let min = Math.min(...values);
    let max = Math.max(...values);

    if (min === max) {
      min = min - 1;
      max = max + 1;
      return { min, max };
    }

    const padding = (max - min) * 0.08;

    return {
      min: min - padding,
      max: max + padding
    };
  }

  private formatDateTime(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString('ro-RO', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  private formatTime(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleTimeString('ro-RO', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}