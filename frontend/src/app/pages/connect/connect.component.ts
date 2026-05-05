import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { ApiService, ConnectRequest } from '../../services/api.service';

@Component({
  selector: 'app-connect',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './connect.component.html',
  styleUrl: './connect.component.css'
})
export class ConnectComponent {
  form: ConnectRequest = {
    broker_address: '192.168.100.18',
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
    private api: ApiService,
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

    this.api.connect(this.form).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        this.loading = false;
        this.errorMessage = err?.error?.detail || 'Connection failed.';
      }
    });
  }
}