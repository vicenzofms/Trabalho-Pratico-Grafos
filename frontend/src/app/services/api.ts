import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import {
  GrafoResumo,
  GrafoVisualizacao,
  JobMineracao,
  RelatorioAnalise,
  RepositorioResumo,
  TipoGrafo,
  TipoRepresentacao,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class Api {
  private http = inject(HttpClient);
  private base = environment.apiBase;

  listarRepositorios() {
    return this.http.get<RepositorioResumo[]>(`${this.base}/repositorios`);
  }

  resumoGrafos(owner: string, repo: string, representacao: TipoRepresentacao = 'matriz') {
    return this.http.get<GrafoResumo[]>(
      `${this.base}/repositorios/${owner}/${repo}/grafos`,
      { params: { representacao } }
    );
  }

  analise(owner: string, repo: string, tipo: TipoGrafo = 'integrado', representacao: TipoRepresentacao = 'matriz') {
    return this.http.get<RelatorioAnalise>(
      `${this.base}/repositorios/${owner}/${repo}/analise`,
      { params: { tipo, representacao } }
    );
  }

  visualizarGrafo(owner: string, repo: string, tipo: TipoGrafo, representacao: TipoRepresentacao = 'matriz') {
    return this.http.get<GrafoVisualizacao>(
      `${this.base}/repositorios/${owner}/${repo}/grafos/${tipo}/visualizacao`,
      { params: { representacao } }
    );
  }

  urlGephi(owner: string, repo: string, tipo: TipoGrafo, representacao: TipoRepresentacao = 'matriz') {
    return `${this.base}/repositorios/${owner}/${repo}/grafos/${tipo}/gephi?representacao=${representacao}`;
  }

  baixarGephi(owner: string, repo: string, tipo: TipoGrafo, representacao: TipoRepresentacao = 'matriz') {
    return this.http.get(
      `${this.base}/repositorios/${owner}/${repo}/grafos/${tipo}/gephi`,
      { params: { representacao }, responseType: 'blob' }
    );
  }

  minerar(owner: string, repo: string) {
    return this.http.post<JobMineracao>(`${this.base}/repositorios/${owner}/${repo}/minerar`, {});
  }

  atualizar(owner: string, repo: string) {
    return this.http.post<JobMineracao>(`${this.base}/repositorios/${owner}/${repo}/atualizar`, {});
  }

  statusMineracao(owner: string, repo: string, jobId: string) {
    return this.http.get<JobMineracao>(
      `${this.base}/repositorios/${owner}/${repo}/minerar/status`,
      { params: { job_id: jobId } }
    );
  }

  excluir(owner: string, repo: string) {
    return this.http.delete<void>(`${this.base}/repositorios/${owner}/${repo}`);
  }
}
