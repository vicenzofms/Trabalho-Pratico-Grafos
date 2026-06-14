import { Component, DestroyRef, effect, inject, input, output } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

// Contador compartilhado entre instâncias: trava o scroll do body enquanto
// houver ao menos um modal aberto (suporta modais empilhados).
let modaisAbertos = 0;
let lockAtivo = false;
let bodyOverflowAnterior = '';
let bodyOverscrollAnterior = '';
let htmlOverflowAnterior = '';
let htmlOverscrollAnterior = '';

function atualizarLockBody() {
  if (typeof document === 'undefined') return;
  const { body, documentElement } = document;
  if (modaisAbertos > 0) {
    if (lockAtivo) return;
    lockAtivo = true;
    bodyOverflowAnterior = body.style.overflow;
    bodyOverscrollAnterior = body.style.overscrollBehavior;
    htmlOverflowAnterior = documentElement.style.overflow;
    htmlOverscrollAnterior = documentElement.style.overscrollBehavior;
    body.style.overflow = 'hidden';
    body.style.overscrollBehavior = 'none';
    documentElement.style.overflow = 'hidden';
    documentElement.style.overscrollBehavior = 'none';
    return;
  }

  if (!lockAtivo) return;
  lockAtivo = false;
  body.style.overflow = bodyOverflowAnterior;
  body.style.overscrollBehavior = bodyOverscrollAnterior;
  documentElement.style.overflow = htmlOverflowAnterior;
  documentElement.style.overscrollBehavior = htmlOverscrollAnterior;
}

/**
 * Overlay modal reutilizável (sem CDK). Fecha no backdrop e no Esc, anima ao abrir
 * e trava o scroll da página enquanto aberto.
 * Corpo via `<ng-content>`; rodapé opcional via `<ng-content select="[footer]">`.
 */
@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    @if (aberto()) {
      <div
        class="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-black/65"
        style="animation: modalFade 0.2s ease-out both"
        animate.leave="modal-overlay-leave"
        (click)="fechar.emit()"
        (keydown.escape)="fechar.emit()"
        tabindex="-1"
      >
        <div
          class="nb-border-3 nb-shadow-lg rounded-[6px] bg-surface w-full max-w-lg max-h-[85vh] flex flex-col nb-themed"
          style="animation: modalPop 0.22s var(--ease-out, ease-out) both"
          animate.leave="modal-panel-leave"
          (click)="$event.stopPropagation()"
          role="dialog"
          aria-modal="true"
        >
          <div class="flex items-center justify-between gap-4 p-5 border-b-[3px] border-ink">
            <h2 class="font-bold text-lg">{{ titulo() }}</h2>
            <button
              (click)="fechar.emit()"
              class="opacity-70 hover:opacity-100 cursor-pointer"
              aria-label="Fechar"
            >
              <lucide-icon name="x" class="w-5 h-5" />
            </button>
          </div>

          <div class="p-5 overflow-y-auto flex-1">
            <ng-content />
          </div>

          @if (comRodape()) {
            <div class="p-5 border-t-[3px] border-ink flex justify-end gap-3 flex-shrink-0">
              <ng-content select="[footer]" />
            </div>
          }
        </div>
      </div>
    }
  `,
})
export class Modal {
  aberto = input(false);
  titulo = input('');
  comRodape = input(true);
  fechar = output<void>();

  private travado = false;

  constructor() {
    effect(() => {
      const aberto = this.aberto();
      if (aberto === this.travado) return; // só reage a transições reais
      this.travado = aberto;
      modaisAbertos = Math.max(0, modaisAbertos + (aberto ? 1 : -1));
      atualizarLockBody();
    });

    inject(DestroyRef).onDestroy(() => {
      if (this.travado) {
        modaisAbertos = Math.max(0, modaisAbertos - 1);
        atualizarLockBody();
      }
    });
  }
}
