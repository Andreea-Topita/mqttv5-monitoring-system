export interface SensorMeasurementItem {
  id: number;
  mqtt_message_id: number | null;
  topic: string;
  source_client_id: string | null;
  base_name: string | null;
  measurement_name: string;
  unit: string;
  numeric_value: number;
  measured_at: string;
  created_at: string;
}

export interface SensorMeasurementsResponse {
  success: boolean;
  data: SensorMeasurementItem[];
}