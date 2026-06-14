import { effect, Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class Theme {
  readonly tema = signal<'dark' | 'light'>(
    (localStorage.getItem('tema') as 'dark' | 'light') ?? 'dark'
  );

  constructor() {
    effect(() => {
      const t = this.tema();
      document.documentElement.classList.toggle('dark', t === 'dark');
      localStorage.setItem('tema', t);
    });
  }

  alternar() {
    const trocar = () => this.tema.update(t => (t === 'dark' ? 'light' : 'dark'));
    const reduz = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if ((document as any).startViewTransition && !reduz) {
      (document as any).startViewTransition(trocar);
    } else {
      trocar();
    }
  }
}
