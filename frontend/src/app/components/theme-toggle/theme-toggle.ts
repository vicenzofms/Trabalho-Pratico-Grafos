import { Component, inject } from '@angular/core';
import { LucideAngularModule, Sun, Moon } from 'lucide-angular';
import { Theme } from '../../services/theme';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <button
      (click)="theme.alternar()"
      class="nb-border nb-shadow-sm nb-themed nb-interactive grid place-items-center size-10 bg-surface text-foreground cursor-pointer rounded-[6px]"
      [attr.aria-label]="theme.tema() === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro'"
    >
      <lucide-icon
        [img]="theme.tema() === 'dark' ? Sun : Moon"
        [size]="20"
        class="transition-transform duration-300"
        [class.rotate-180]="theme.tema() === 'light'"
      />
    </button>
  `,
})
export class ThemeToggle {
  theme = inject(Theme);
  Sun = Sun;
  Moon = Moon;
}
