import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ThemeToggle } from './components/theme-toggle/theme-toggle';
import { Repositorio } from './services/repositorio';
import { Theme } from './services/theme';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ThemeToggle],
  templateUrl: './app.html',
})
export class App {
  repositorio = inject(Repositorio);
  theme = inject(Theme);
}
