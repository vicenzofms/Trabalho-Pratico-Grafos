import { Component, computed, inject, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Repositorio } from '../../services/repositorio';
import { ToastService } from '../../services/toast';
import { StatusView } from '../../components/status-view/status-view';
import { Modal } from '../../components/modal/modal';
import { Tooltip } from '../../components/tooltip/tooltip';
import { environment } from '../../../environments/environment';
import { RepositorioResumo, TipoRepresentacao } from '../../models/api.models';

@Component({
  selector: 'app-repositorios',
  standalone: true,
  imports: [StatusView, Modal, Tooltip, NgClass, LucideAngularModule],
  templateUrl: './repositorios.html',
})
export class Repositorios {
  private router = inject(Router);
  private toast = inject(ToastService);
  repositorio = inject(Repositorio);

  mineracaoHabilitada = environment.mineracaoHabilitada;

  inputRepo = signal('');
  inputErro = signal('');

  // Modais
  modalAnalisar = signal<RepositorioResumo | null>(null);
  representacaoEscolhida = signal<TipoRepresentacao>('matriz');
  modalAtualizar = signal<RepositorioResumo | null>(null);
  modalExcluir = signal<RepositorioResumo | null>(null);

  repos = this.repositorio.repositorios;

  /** Repos em mineração que ainda não aparecem na lista (ex.: repo novo sem cache). */
  cardsMineracaoNova = computed(() => {
    const nomes = new Set((this.repos.value() ?? []).map(r => r.nome));
    return [...this.repositorio.emMineracao()].filter(n => !nomes.has(n));
  });

  get errorMsg() {
    const e = this.repos.error() as any;
    if (!e) return null;
    return e?.message ?? e?.error?.detail ?? `HTTP ${e?.status ?? 'error'}`;
  }

  get listaVazia() {
    return (
      !this.repos.isLoading() &&
      !this.repos.error() &&
      !this.repos.value()?.length &&
      !this.cardsMineracaoNova().length
    );
  }

  /** Aceita `owner/repo`, URL do GitHub (https/sem protocolo) ou SSH. */
  parseRepo(entrada: string): string | null {
    const v = entrada.trim();
    if (!v) return null;
    const ssh = v.match(/^git@github\.com:([^/\s]+)\/([^/\s]+?)(?:\.git)?\/?$/i);
    if (ssh) return `${ssh[1]}/${ssh[2]}`;
    const url = v.match(/^(?:https?:\/\/)?(?:www\.)?github\.com\/([^/\s]+)\/([^/\s#?]+)/i);
    if (url) return `${url[1]}/${url[2].replace(/\.git$/i, '')}`;
    const simples = v.match(/^([\w.-]+)\/([\w.-]+?)(?:\.git)?$/);
    if (simples) return `${simples[1]}/${simples[2]}`;
    return null;
  }

  validarInput(): string | null {
    const nome = this.parseRepo(this.inputRepo());
    if (!nome) {
      this.inputErro.set('Formato inválido. Use owner/repo ou a URL do GitHub.');
      return null;
    }
    if (this.repos.value()?.some(r => r.nome === nome) || this.repositorio.estaMinerando(nome)) {
      this.inputErro.set('Repositório já está na lista ou em mineração.');
      return null;
    }
    this.inputErro.set('');
    return nome;
  }

  async minerar() {
    const nome = this.validarInput();
    if (!nome) return;
    const [owner, repo] = nome.split('/');
    this.inputRepo.set('');
    try {
      await this.repositorio.minerarEAcompanhar(owner, repo);
    } catch (e) {
      this.toast.erro(this.mensagemErro(e, `Não foi possível minerar ${nome}.`));
    }
  }

  // --- Analisar (escolha de representação) ---
  analisar(repo: RepositorioResumo) {
    if (repo.estado !== 'disponivel' || this.minerandoRepo(repo.nome)) return;
    this.representacaoEscolhida.set('matriz');
    this.modalAnalisar.set(repo);
  }

  confirmarAnalise() {
    const repo = this.modalAnalisar();
    if (!repo) return;
    const [owner, name] = repo.nome.split('/');
    this.repositorio.selecionar(owner, name, this.representacaoEscolhida());
    this.modalAnalisar.set(null);
    this.router.navigate([`/${owner}/${name}/visao-geral`]);
  }

  // --- Atualizar (confirmação de remineração) ---
  atualizar(repo: RepositorioResumo) {
    if (repo.estado !== 'disponivel' || this.minerandoRepo(repo.nome)) return;
    this.modalAtualizar.set(repo);
  }

  async confirmarAtualizar() {
    const repo = this.modalAtualizar();
    if (!repo) return;
    this.modalAtualizar.set(null);
    const [owner, name] = repo.nome.split('/');
    try {
      await this.repositorio.minerarEAcompanhar(owner, name, true);
    } catch (e) {
      this.toast.erro(this.mensagemErro(e, `Não foi possível atualizar ${repo.nome}.`));
    }
  }

  // --- Excluir (repositório + cache) ---
  excluir(repo: RepositorioResumo) {
    if (this.minerandoRepo(repo.nome)) return;
    this.modalExcluir.set(repo);
  }

  async confirmarExcluir() {
    const repo = this.modalExcluir();
    if (!repo) return;
    this.modalExcluir.set(null);
    const [owner, name] = repo.nome.split('/');
    try {
      await this.repositorio.excluir(owner, name);
      this.toast.sucesso(`Repositório ${repo.nome} excluído.`);
    } catch (e) {
      this.toast.erro(this.mensagemErro(e, `Não foi possível excluir ${repo.nome}.`));
    }
  }

  private mensagemErro(e: any, padrao: string): string {
    return e?.error?.detail ?? e?.message ?? padrao;
  }

  minerandoRepo(nome: string): boolean {
    return (
      this.repositorio.estaMinerando(nome) ||
      this.repos.value()?.find(r => r.nome === nome)?.estado === 'minerando'
    );
  }

  /** Estado mostrado: "minerando" sobrepõe o estado do backend enquanto o job roda. */
  estadoEfetivo(repo: RepositorioResumo): string {
    return this.minerandoRepo(repo.nome) ? 'minerando' : repo.estado;
  }

  badgeClasse(estado: string) {
    const map: Record<string, string> = {
      disponivel: 'bg-tertiary text-on-tertiary',
      ausente:    'bg-muted/20 text-muted',
      minerando:  'bg-secondary text-on-secondary',
      erro:       'bg-danger text-white',
    };
    return map[estado] ?? 'bg-muted/20 text-muted';
  }

  badgeLabel(estado: string) {
    const map: Record<string, string> = {
      disponivel: 'Disponível',
      ausente:    'Ausente',
      minerando:  'Minerando...',
      erro:       'Erro',
    };
    return map[estado] ?? estado;
  }

  formatarCacheadoEm(valor: string | null): string {
    if (!valor) return '—';
    return new Intl.DateTimeFormat('pt-BR').format(new Date(valor));
  }

  retry() {
    this.repos.reload();
  }
}
