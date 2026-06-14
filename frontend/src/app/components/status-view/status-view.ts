import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-status-view',
  standalone: true,
  template: `
    @if (loading()) {
      <div class="space-y-4">
        @for (i of skeletons(); track i) {
          <div class="nb-border nb-shadow rounded-[6px] p-5 bg-surface animate-pulse">
            <div class="h-5 bg-muted/20 rounded mb-3 w-1/3"></div>
            <div class="h-4 bg-muted/20 rounded mb-2 w-1/2"></div>
            <div class="h-4 bg-muted/20 rounded w-1/4"></div>
          </div>
        }
      </div>
    } @else if (error()) {
      <div class="nb-border-3 nb-shadow bg-danger text-white rounded-[6px] p-5 flex items-start gap-4">
        <span class="text-2xl">!</span>
        <div class="flex-1">
          <p class="font-bold mb-1">Erro ao carregar dados</p>
          <p class="text-sm opacity-90 mb-3">{{ error() }}</p>
          <button
            (click)="retry.emit()"
            class="nb-border nb-shadow-sm nb-interactive bg-white text-danger font-semibold px-4 py-1.5 rounded-[6px] cursor-pointer text-sm"
          >
            Tentar de novo
          </button>
        </div>
      </div>
    } @else if (empty()) {
      <div class="nb-border nb-shadow rounded-[6px] p-10 bg-surface text-center">
        <p class="text-4xl mb-4">📭</p>
        <p class="font-bold text-lg mb-2">{{ emptyTitle() }}</p>
        <p class="text-muted text-sm">{{ emptyMessage() }}</p>
      </div>
    }
  `,
})
export class StatusView {
  loading = input(false);
  error = input<string | null>(null);
  empty = input(false);
  emptyTitle = input('Nenhum dado encontrado');
  emptyMessage = input('');
  skeletonCount = input(3);
  retry = output<void>();

  skeletons() {
    return Array.from({ length: this.skeletonCount() }, (_, i) => i);
  }
}
