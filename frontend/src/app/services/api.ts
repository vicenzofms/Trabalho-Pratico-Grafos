import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import {
  GrafoResumo,
  JobMineracao,
  RelatorioAnalise,
  RepositorioResumo,
  TipoGrafo,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class Api {
  private http = inject(HttpClient);
  private base = environment.apiBase;

  listarRepositorios() {
    return this.http.get<RepositorioResumo[]>(`${this.base}/repositorios`);
  }

  resumoGrafos(owner: string, repo: string) {
    return this.http.get<GrafoResumo[]>(`${this.base}/repositorios/${owner}/${repo}/grafos`);
  }

  analise(owner: string, repo: string) {
    return this.http.get<RelatorioAnalise>(`${this.base}/repositorios/${owner}/${repo}/analise`);
  }

  urlGephi(owner: string, repo: string, tipo: TipoGrafo) {
    return `${this.base}/repositorios/${owner}/${repo}/grafos/${tipo}/gephi`;
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
}
