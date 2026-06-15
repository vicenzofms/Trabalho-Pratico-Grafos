import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';
import { Repositorio } from '../../services/repositorio';
import { ToastService } from '../../services/toast';
import { StatusView } from '../../components/status-view/status-view';
import { Api } from '../../services/api';
import { TipoGrafo } from '../../models/api.models';

@Component({
  selector: 'app-visao-geral',
  standalone: true,
  imports: [StatusView, RouterLink, LucideAngularModule],
  templateUrl: './visao-geral.html',
})
export class VisaoGeral implements OnInit {
  private route = inject(ActivatedRoute);
  private api = inject(Api);
  private toast = inject(ToastService);
  repositorio = inject(Repositorio);

  grafos = this.repositorio.grafos;

  baixando = signal<Set<TipoGrafo>>(new Set());

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

  linkMetricas(tipo: TipoGrafo): any[] {
    const sel = this.repositorio.selecionado();
    if (!sel) return ['/'];
    return ['/', sel.owner, sel.repo, 'metricas', tipo];
  }

  estaBaixando(tipo: TipoGrafo) {
    return this.baixando().has(tipo);
  }

  async baixarGephi(tipo: TipoGrafo) {
    const sel = this.repositorio.selecionado();
    if (!sel || this.baixando().has(tipo)) return;
    this.baixando.update(s => new Set(s).add(tipo));
    try {
      const blob = await firstValueFrom(
        this.api.baixarGephi(sel.owner, sel.repo, tipo, this.repositorio.representacao())
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${sel.owner}_${sel.repo}_${tipo}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      this.toast.erro(`Falha ao exportar GEPHI (${this.tipoLabel(tipo)}).`);
    } finally {
      this.baixando.update(s => {
        const n = new Set(s);
        n.delete(tipo);
        return n;
      });
    }
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
