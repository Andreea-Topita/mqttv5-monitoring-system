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
    broker_address: 'localhost',
    broker_port: 1883,
    client_id: 'mqtt',
    username: '',
    password: '',
    last_will_topic: 'Cpu load',
    last_will_message: 'Clientul s-a deconectat.',
    last_will_qos: 0,
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
      !this.form.client_id ||
      !this.form.username ||
      !this.form.password
    ) {
      this.errorMessage = 'Toate campurile importante trebuie completate.';
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
        this.errorMessage = err?.error?.detail || 'Conectarea a esuat.';
      }
    });
  }
}