import { Injectable, signal } from '@angular/core';

/** Dispara o overlay de confeti (ex.: ao concluir uma mineração). */
@Injectable({ providedIn: 'root' })
export class ConfettiService {
  readonly disparos = signal(0);

  disparar() {
    this.disparos.update(n => n + 1);
  }
}
