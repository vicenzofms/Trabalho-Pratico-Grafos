import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

/** Ícone "i" com tooltip on-hover (CSS group-hover, sem lib). */
@Component({
  selector: 'app-info-hint',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <span class="group relative inline-flex items-center align-middle">
      <lucide-icon name="info" class="w-4 h-4 text-muted cursor-help" aria-hidden="true" />
      <span
        class="pointer-events-none absolute z-50 left-1/2 -translate-x-1/2 bottom-full mb-2 w-56
               opacity-0 group-hover:opacity-100 transition-opacity duration-150
               nb-border nb-shadow-sm rounded-[6px] bg-surface text-foreground
               text-xs font-normal normal-case tracking-normal leading-snug p-2 text-left"
        role="tooltip"
      >
        {{ texto() }}
      </span>
    </span>
  `,
})
export class InfoHint {
  texto = input('');
}
