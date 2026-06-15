import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/repositorios/repositorios').then(m => m.Repositorios),
  },
  {
    path: ':owner/:repo/visao-geral',
    loadComponent: () =>
      import('./pages/visao-geral/visao-geral').then(m => m.VisaoGeral),
  },
  {
    path: ':owner/:repo/metricas/:tipo',
    loadComponent: () =>
      import('./pages/metricas/metricas').then(m => m.Metricas),
  },
  { path: '**', redirectTo: '' },
];
