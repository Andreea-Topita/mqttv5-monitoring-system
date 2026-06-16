export interface DisplayMqttPayload {
  isFormatted: boolean;
  label: string;
  valueText: string;
  device?: string;
  measuredAt?: string;
  rawPayload: string;
}

interface SenmlRecord {
  bn?: string;
  n?: string;
  u?: string;
  v?: number | string;
  t?: number | string;
}

const SENSOR_LABELS: Record<string, string> = {
  temperature: 'Temperature',
  humidity: 'Humidity'
};

export function formatMqttPayload(
  topic: string,
  payload: string,
  fallbackTimestamp?: number
): DisplayMqttPayload {
  const rawPayload = payload ?? '';

  const topicInfo = parseDeviceTopic(topic);

  if (topicInfo?.category === 'status') {
    return {
      isFormatted: true,
      label: 'Status',
      valueText: rawPayload || '-',
      device: topicInfo.clientId,
      measuredAt: formatTimestamp(fallbackTimestamp),
      rawPayload
    };
  }

  const senmlRecord = parseSenmlPayload(rawPayload);

  if (!senmlRecord) {
    return {
      isFormatted: false,
      label: 'Payload',
      valueText: rawPayload || '-',
      measuredAt: formatTimestamp(fallbackTimestamp),
      rawPayload
    };
  }

  const measurementName = senmlRecord.n ?? 'measurement';
  const label = SENSOR_LABELS[measurementName] ?? measurementName;
  const valueText = formatMeasurementValue(senmlRecord.v, senmlRecord.u);
  const device = formatDeviceName(senmlRecord.bn) ?? topicInfo?.clientId;
  const measuredAt = formatTimestamp(fallbackTimestamp ?? senmlRecord.t);

  return {
    isFormatted: true,
    label,
    valueText,
    device,
    measuredAt,
    rawPayload
  };
}

export function formatTelemetryValue(topic: string, payload: string): string {
  const formatted = formatMqttPayload(topic, payload);

  if (formatted.isFormatted) {
    return formatted.valueText;
  }

  return payload || '-';
}

function parseDeviceTopic(topic: string): { clientId: string; category: string } | null {
  const parts = topic.split('/');

  if (parts.length !== 3) {
    return null;
  }

  if (parts[0] !== 'licenta') {
    return null;
  }

  return {
    clientId: parts[1],
    category: parts[2]
  };
}

function parseSenmlPayload(payload: string): SenmlRecord | null {
  try {
    const parsed = JSON.parse(payload);

    if (!Array.isArray(parsed) || parsed.length === 0) {
      return null;
    }

    const firstRecord = parsed[0];

    if (!firstRecord || typeof firstRecord !== 'object') {
      return null;
    }

    if (
      firstRecord.n === undefined ||
      firstRecord.v === undefined ||
      firstRecord.u === undefined
    ) {
      return null;
    }

    return firstRecord as SenmlRecord;
  } catch {
    return null;
  }
}

function formatMeasurementValue(value: number | string | undefined, unit: string | undefined): string {
  if (value === undefined || value === null) {
    return '-';
  }

  const numericValue = Number(value);
  const displayValue = Number.isFinite(numericValue)
    ? formatNumber(numericValue)
    : String(value);

  return unit ? `${displayValue} ${unit}` : displayValue;
}

function formatNumber(value: number): string {
  if (Number.isInteger(value)) {
    return value.toString();
  }

  return value.toFixed(2);
}

function formatDeviceName(baseName: string | undefined): string | undefined {
  if (!baseName) {
    return undefined;
  }

  return baseName
    .replace(/^urn:dev:/, '')
    .replace(/:$/, '');
}

function formatTimestamp(timestamp: number | string | undefined): string | undefined {
  if (timestamp === undefined || timestamp === null) {
    return undefined;
  }

  const numericTimestamp = Number(timestamp);

  if (!Number.isFinite(numericTimestamp)) {
    return undefined;
  }

  const milliseconds = numericTimestamp > 1000000000000
    ? numericTimestamp
    : numericTimestamp * 1000;

  return new Date(milliseconds).toLocaleTimeString('ro-RO', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}