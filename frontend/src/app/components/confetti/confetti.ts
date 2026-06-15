import { Component, effect, inject, signal } from '@angular/core';
import { ConfettiService } from '../../services/confetti';

interface Particula {
  id: number;
  left: number;
  emoji: string;
  dx: string;
  dy: string;
  rot: string;
  dur: string;
  delay: string;
}

const EMOJIS = ['🎉', '🎊', '✨', '🥳', '⭐', '🎈'];

/** Explosão de confeti via emoji, acionada pelo ConfettiService. */
@Component({
  selector: 'app-confetti',
  standalone: true,
  template: `
    @if (particulas().length) {
      <div class="fixed inset-0 pointer-events-none z-[95] overflow-hidden" aria-hidden="true">
        @for (p of particulas(); track p.id) {
          <span
            class="absolute top-[15%] text-3xl select-none"
            [style.left.%]="p.left"
            [style.--dx]="p.dx"
            [style.--dy]="p.dy"
            [style.--rot]="p.rot"
            [style.animation]="'confettiFly ' + p.dur + ' var(--ease-out, ease-out) forwards'"
            [style.animation-delay]="p.delay"
          >
            {{ p.emoji }}
          </span>
        }
      </div>
    }
  `,
})
export class ConfettiComponent {
  private confetti = inject(ConfettiService);
  particulas = signal<Particula[]>([]);
  private seq = 0;

  constructor() {
    effect(() => {
      // Re-roda a cada incremento de `disparos()`; ignora o valor inicial (0).
      if (this.confetti.disparos() === 0) return;
      this.explodir();
    });
  }

  private explodir() {
    const novas: Particula[] = Array.from({ length: 56 }, () => ({
      id: this.seq++,
      left: 8 + Math.random() * 84,
      emoji: EMOJIS[Math.floor(Math.random() * EMOJIS.length)],
      dx: `${(Math.random() * 760 - 380).toFixed(0)}px`,
      dy: `${(220 + Math.random() * 520).toFixed(0)}px`,
      rot: `${(Math.random() * 960 - 480).toFixed(0)}deg`,
      dur: `${(2.1 + Math.random() * 1.1).toFixed(2)}s`,
      delay: `${(Math.random() * 0.25).toFixed(2)}s`,
    }));
    this.particulas.set(novas);
    setTimeout(() => this.particulas.set([]), 3600);
  }
}
