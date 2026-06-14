import { inject, Injectable, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Api } from './api';
import { ToastService } from './toast';
import { ConfettiService } from './confetti';
import {
  GrafoResumo,
  RelatorioAnalise,
  RepositorioResumo,
  TipoGrafo,
  TipoRepresentacao,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class Repositorio {
  private base = environment.apiBase;
  private api = inject(Api);
  private toast = inject(ToastService);
  private confetti = inject(ConfettiService);

  readonly repositorios = httpResource<RepositorioResumo[]>(() => `${this.base}/repositorios`);

  readonly selecionado = signal<{ owner: string; repo: string } | null>(null);
  /** Representação interna escolhida no "Analisar" (afeta os 4 grafos do repo). */
  readonly representacao = signal<TipoRepresentacao>('matriz');
  /** Grafo cujas métricas estão sendo exibidas (página de Métricas). */
  readonly tipoAnalise = signal<TipoGrafo>('integrado');

  /** Repositórios (owner/repo) com mineração em andamento disparada no app. */
  readonly emMineracao = signal<Set<string>>(new Set());

  readonly grafos = httpResource<GrafoResumo[]>(() => {
    const s = this.selecionado();
    if (!s) return undefined;
    return `${this.base}/repositorios/${s.owner}/${s.repo}/grafos?representacao=${this.representacao()}`;
  });

  readonly analise = httpResource<RelatorioAnalise>(() => {
    const s = this.selecionado();
    if (!s) return undefined;
    return `${this.base}/repositorios/${s.owner}/${s.repo}/analise?tipo=${this.tipoAnalise()}&representacao=${this.representacao()}`;
  });

  selecionar(owner: string, repo: string, representacao?: TipoRepresentacao) {
    if (representacao) this.representacao.set(representacao);
    this.selecionado.set({ owner, repo });
  }

  estaMinerando(nome: string): boolean {
    return this.emMineracao().has(nome);
  }

  /** Exclui o repositório e seu cache, recarregando a lista. Erro é propagado. */
  async excluir(owner: string, repo: string) {
    await firstValueFrom(this.api.excluir(owner, repo));
    this.repositorios.reload();
  }

  private adicionar(chave: string) {
    this.emMineracao.update(s => new Set(s).add(chave));
  }

  private remover(chave: string) {
    this.emMineracao.update(s => {
      const n = new Set(s);
      n.delete(chave);
      return n;
    });
  }

  /** Dispara mineração/atualização e acompanha até concluir. Erros do POST são propagados. */
  async minerarEAcompanhar(owner: string, repo: string, atualizar = false) {
    const chave = `${owner}/${repo}`;
    this.adicionar(chave);
    let jobId: string;
    try {
      const job = await firstValueFrom(
        atualizar ? this.api.atualizar(owner, repo) : this.api.minerar(owner, repo)
      );
      jobId = job.job_id;
    } catch (e) {
      this.remover(chave);
      throw e;
    }
    this.repositorios.reload();
    this.poll(owner, repo, jobId);
  }

  private async poll(owner: string, repo: string, jobId: string) {
    const chave = `${owner}/${repo}`;
    try {
      const s = await firstValueFrom(this.api.statusMineracao(owner, repo, jobId));
      if (s.estado === 'concluido' || s.estado === 'erro') {
        this.remover(chave);
        this.repositorios.reload();
        if (s.estado === 'erro') {
          this.toast.erro(`Falha ao minerar ${chave}: ${s.detalhe ?? 'erro desconhecido'}`);
        } else {
          this.toast.sucesso(`Mineração de ${chave} concluída.`);
          this.confetti.disparar();
        }
        return;
      }
      setTimeout(() => this.poll(owner, repo, jobId), 2500);
    } catch {
      this.remover(chave);
      this.repositorios.reload();
      this.toast.erro(`Erro ao acompanhar a mineração de ${chave}.`);
    }
  }
}
