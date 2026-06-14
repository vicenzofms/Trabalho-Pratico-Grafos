import { inject, Injectable, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Api } from './api';
import { GrafoResumo, RelatorioAnalise, RepositorioResumo } from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class Repositorio {
  private base = environment.apiBase;
  private api = inject(Api);

  readonly repositorios = httpResource<RepositorioResumo[]>(() => `${this.base}/repositorios`);

  readonly selecionado = signal<{ owner: string; repo: string } | null>(null);

  readonly grafos = httpResource<GrafoResumo[]>(() => {
    const s = this.selecionado();
    return s ? `${this.base}/repositorios/${s.owner}/${s.repo}/grafos` : undefined;
  });

  readonly analise = httpResource<RelatorioAnalise>(() => {
    const s = this.selecionado();
    return s ? `${this.base}/repositorios/${s.owner}/${s.repo}/analise` : undefined;
  });

  selecionar(owner: string, repo: string) {
    this.selecionado.set({ owner, repo });
  }

  async minerarEAcompanhar(owner: string, repo: string, atualizar = false) {
    const job = await firstValueFrom(
      atualizar ? this.api.atualizar(owner, repo) : this.api.minerar(owner, repo)
    );
    this.poll(owner, repo, job.job_id);
  }

  private async poll(owner: string, repo: string, jobId: string) {
    const s = await firstValueFrom(this.api.statusMineracao(owner, repo, jobId));
    if (s.estado === 'concluido' || s.estado === 'erro') {
      this.repositorios.reload();
      return;
    }
    setTimeout(() => this.poll(owner, repo, jobId), 2500);
  }
}
