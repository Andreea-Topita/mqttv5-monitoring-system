import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { SensorMeasurementsResponse } from '../models/sensor-measurement.models';

@Injectable({
  providedIn: 'root'
})
export class SensorMeasurementApiService {
  private baseUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getMeasurements(
    measurementName?: string,
    topic?: string,
    sourceClientId?: string,
    limit: number = 50
  ) {
    let params = new HttpParams().set('limit', limit);

    if (measurementName) {
      params = params.set('measurement_name', measurementName);
    }

    if (topic) {
      params = params.set('topic', topic);
    }

    if (sourceClientId) {
      params = params.set('source_client_id', sourceClientId);
    }

    return this.http.get<SensorMeasurementsResponse>(
      `${this.baseUrl}/api/sensor-measurements`,
      { params }
    );
  }
}