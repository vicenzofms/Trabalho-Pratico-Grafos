import { Component, inject, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { Router } from '@angular/router';
import { Repositorio } from '../../services/repositorio';
import { StatusView } from '../../components/status-view/status-view';
import { environment } from '../../../environments/environment';
import { RepositorioResumo } from '../../models/api.models';

@Component({
  selector: 'app-repositorios',
  standalone: true,
  imports: [StatusView, NgClass],
  templateUrl: './repositorios.html',
})
export class Repositorios {
  private router = inject(Router);
  repositorio = inject(Repositorio);

  mineracaoHabilitada = environment.mineracaoHabilitada;

  inputRepo = signal('');
  inputErro = signal('');
  minerando = signal<Set<string>>(new Set());

  repos = this.repositorio.repositorios;

  get errorMsg() {
    const e = this.repos.error() as any;
    if (!e) return null;
    return e?.message ?? e?.error?.detail ?? `HTTP ${e?.status ?? 'error'}`;
  }

  get listaVazia() {
    return !this.repos.isLoading() && !this.repos.error() && !this.repos.value()?.length;
  }

  analisar(repo: RepositorioResumo) {
    const [owner, name] = repo.nome.split('/');
    this.repositorio.selecionar(owner, name);
    this.router.navigate([`/${owner}/${name}/visao-geral`]);
  }

  validarInput(): boolean {
    const v = this.inputRepo().trim();
    if (!/^[\w.-]+\/[\w.-]+$/.test(v)) {
      this.inputErro.set('Formato inválido. Use owner/repo');
      return false;
    }
    const existe = this.repos.value()?.some(r => r.nome === v);
    if (existe) {
      this.inputErro.set('Repositório já existe na lista');
      return false;
    }
    this.inputErro.set('');
    return true;
  }

  async minerar() {
    if (!this.validarInput()) return;
    const [owner, repo] = this.inputRepo().trim().split('/');
    const chave = `${owner}/${repo}`;
    this.minerando.update(s => new Set(s).add(chave));
    this.inputRepo.set('');
    try {
      await this.repositorio.minerarEAcompanhar(owner, repo);
    } finally {
      this.minerando.update(s => { const n = new Set(s); n.delete(chave); return n; });
    }
  }

  async atualizar(repo: RepositorioResumo) {
    const [owner, name] = repo.nome.split('/');
    const chave = repo.nome;
    this.minerando.update(s => new Set(s).add(chave));
    try {
      await this.repositorio.minerarEAcompanhar(owner, name, true);
    } finally {
      this.minerando.update(s => { const n = new Set(s); n.delete(chave); return n; });
    }
  }

  estaMinrando(nome: string) {
    return this.minerando().has(nome) || (this.repos.value()?.find(r => r.nome === nome)?.estado === 'minerando');
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

  retry() {
    this.repos.reload();
  }
}
