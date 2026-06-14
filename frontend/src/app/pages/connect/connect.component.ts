import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { timeout } from 'rxjs';

import { MqttApiService } from '../../core/services/mqtt-api.service';
import { AuthService } from '../../core/services/auth.service';
import { ConnectRequest } from '../../core/models/mqtt.models';
import { getApiErrorMessage } from '../../core/utils/api-error.util';

@Component({
  selector: 'app-connect',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './connect.component.html',
  styleUrl: './connect.component.css'
})
export class ConnectComponent {
  form: ConnectRequest = {
    broker_address: 'mosquitto',
    broker_port: 1883,
    client_id: 'pc_monitor_01',
    username: '',
    password: '',
    last_will_topic: 'licenta/pc/status',
    last_will_message: 'offline',
    last_will_qos: 1,
    last_will_retain: false
  };

  errorMessage = '';
  loading = false;

  constructor(
    private api: MqttApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  connect() {
    this.errorMessage = '';

    if (
      !this.form.broker_address ||
      !this.form.broker_port ||
      !this.form.client_id
    ) {
      this.errorMessage = 'Broker address, broker port and client ID are required.';
      return;
    }

    this.loading = true;

    this.api.connect(this.form)
      .pipe(timeout(8000))
      .subscribe({
        next: () => {
          this.loading = false;
          this.router.navigate(['/dashboard']);
        },
        error: (err: any) => {
          this.loading = false;

          if (err?.name === 'TimeoutError') {
            this.errorMessage = 'Connection timeout. Check whether the backend API and MQTT broker are running.';
            return;
          }

          if (err?.status === 0) {
            this.errorMessage = 'Cannot reach the backend API. Make sure the server is running on port 8000.';
            return;
          }

          this.errorMessage = getApiErrorMessage(err, 'Connection failed.');
        }
      });
  }
  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}