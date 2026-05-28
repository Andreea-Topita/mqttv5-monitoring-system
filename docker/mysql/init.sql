CREATE TABLE IF NOT EXISTS mqtt_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    payload TEXT NOT NULL,
    qos TINYINT NOT NULL,
    direction VARCHAR(20) NOT NULL,
    source_client_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscription_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    qos TINYINT NOT NULL,
    action VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS connection_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL,
    broker_address VARCHAR(255) NOT NULL,
    broker_port INT NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_measurements (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    mqtt_message_id BIGINT NULL,

    topic VARCHAR(255) NOT NULL,
    source_client_id VARCHAR(100),

    base_name VARCHAR(255),
    measurement_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    numeric_value DOUBLE NOT NULL,

    measured_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sensor_measurements_mqtt_message
        FOREIGN KEY (mqtt_message_id)
        REFERENCES mqtt_messages(id)
        ON DELETE SET NULL,
    
    -- sa caut mai repede cand voi face grafice : ultimele 50 de valori etc
    INDEX idx_sensor_measurements_measurement_time (measurement_name, measured_at),
    INDEX idx_sensor_measurements_topic_time (topic, measured_at),
    INDEX idx_sensor_measurements_source_time (source_client_id, measured_at)
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);