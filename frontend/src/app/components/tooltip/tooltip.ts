import { Component, input } from '@angular/core';

/** Tooltip visual do projeto para substituir o tooltip nativo de `title`. */
@Component({
  selector: 'app-tooltip',
  standalone: true,
  host: { class: 'inline-flex' },
  template: `
    <span class="group relative inline-flex items-center align-middle">
      <ng-content />
      @if (texto()) {
        <span
          class="pointer-events-none absolute z-[100] left-1/2 -translate-x-1/2 bottom-full mb-2 w-max max-w-64
                 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-150
                 nb-border nb-shadow-sm rounded-[6px] bg-surface text-foreground
                 text-xs font-normal normal-case tracking-normal leading-snug px-2 py-1.5 text-left"
          role="tooltip"
        >
          {{ texto() }}
        </span>
      }
    </span>
  `,
})
export class Tooltip {
  texto = input('');
}
