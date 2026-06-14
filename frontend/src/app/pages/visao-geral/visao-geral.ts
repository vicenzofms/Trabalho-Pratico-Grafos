import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Repositorio } from '../../services/repositorio';
import { StatusView } from '../../components/status-view/status-view';
import { Api } from '../../services/api';
import { TipoGrafo } from '../../models/api.models';

@Component({
  selector: 'app-visao-geral',
  standalone: true,
  imports: [StatusView],
  templateUrl: './visao-geral.html',
})
export class VisaoGeral implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private api = inject(Api);
  repositorio = inject(Repositorio);

  grafos = this.repositorio.grafos;

  ngOnInit() {
    const { owner, repo } = this.route.snapshot.params;
    const sel = this.repositorio.selecionado();
    if (!sel || sel.owner !== owner || sel.repo !== repo) {
      this.repositorio.selecionar(owner, repo);
    }
  }

  get errorMsg() {
    const e = this.grafos.error() as any;
    if (!e) return null;
    return e?.message ?? e?.error?.detail ?? `HTTP ${e?.status ?? 'error'}`;
  }

  retry() {
    this.grafos.reload();
  }

  urlGephi(tipo: TipoGrafo) {
    const sel = this.repositorio.selecionado();
    if (!sel) return '#';
    return this.api.urlGephi(sel.owner, sel.repo, tipo);
  }

  chipCorClasse(tipo: TipoGrafo) {
    const map: Record<TipoGrafo, string> = {
      integrado:   'bg-[var(--data-1)] text-white',
      comentarios: 'bg-[var(--data-2)] text-black',
      fechamento:  'bg-[var(--data-3)] text-black',
      prs:         'bg-[var(--data-4)] text-black',
    };
    return map[tipo] ?? 'bg-muted/20 text-muted';
  }

  tipoLabel(tipo: TipoGrafo) {
    const map: Record<TipoGrafo, string> = {
      integrado:   'Integrado',
      comentarios: 'Comentários',
      fechamento:  'Fechamento',
      prs:         'Pull Requests',
    };
    return map[tipo] ?? tipo;
  }
}
