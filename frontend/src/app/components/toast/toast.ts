import { Component, inject } from '@angular/core';
import { NgClass } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ToastService } from '../../services/toast';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [NgClass, LucideAngularModule],
  template: `
    <div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-3 w-[min(92vw,22rem)]">
      @for (t of toast.toasts(); track t.id) {
        <div
          class="nb-border-3 nb-shadow rounded-[6px] p-4 flex items-start gap-3 nb-themed"
          style="animation: fadeInUp 0.25s ease-out both"
          [ngClass]="classe(t.tipo)"
          role="alert"
        >
          <lucide-icon [name]="icone(t.tipo)" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p class="flex-1 text-sm font-semibold break-words">{{ t.mensagem }}</p>
          <button
            (click)="toast.remover(t.id)"
            class="flex-shrink-0 opacity-80 hover:opacity-100 cursor-pointer"
            aria-label="Fechar"
          >
            <lucide-icon name="x" class="w-4 h-4" />
          </button>
        </div>
      }
    </div>

    <style>
      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
      }
    </style>
  `,
})
export class ToastComponent {
  toast = inject(ToastService);

  classe(tipo: string) {
    const map: Record<string, string> = {
      erro: 'bg-danger text-white',
      sucesso: 'bg-tertiary text-on-tertiary',
      info: 'bg-surface text-foreground',
    };
    return map[tipo] ?? 'bg-surface text-foreground';
  }

  icone(tipo: string) {
    const map: Record<string, string> = {
      erro: 'alert-circle',
      sucesso: 'info',
      info: 'info',
    };
    return map[tipo] ?? 'info';
  }
}
