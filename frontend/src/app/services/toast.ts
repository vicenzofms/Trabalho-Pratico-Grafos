import { Injectable, signal } from '@angular/core';

export type ToastTipo = 'erro' | 'sucesso' | 'info';

export interface Toast {
  id: number;
  mensagem: string;
  tipo: ToastTipo;
}

/** Fila simples de toasts (signal). Auto-dismiss após `duracaoMs`. */
@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private proximoId = 0;

  push(mensagem: string, tipo: ToastTipo = 'info', duracaoMs = 5000) {
    const id = this.proximoId++;
    this.toasts.update(lista => [...lista, { id, mensagem, tipo }]);
    if (duracaoMs > 0) {
      setTimeout(() => this.remover(id), duracaoMs);
    }
    return id;
  }

  erro(mensagem: string) {
    return this.push(mensagem, 'erro', 7000);
  }

  sucesso(mensagem: string) {
    return this.push(mensagem, 'sucesso');
  }

  remover(id: number) {
    this.toasts.update(lista => lista.filter(t => t.id !== id));
  }
}
