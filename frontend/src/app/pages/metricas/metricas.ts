import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Repositorio } from '../../services/repositorio';
import { StatusView } from '../../components/status-view/status-view';
import { RankingTable } from '../../components/ranking-table/ranking-table';
import { ItemRanking } from '../../models/api.models';

type MetricaChave = 'grau_entrada' | 'grau_saida' | 'pagerank' | 'autovetor' | 'proximidade' | 'intermediacao';

const METRICAS: { chave: MetricaChave; label: string }[] = [
  { chave: 'grau_entrada',   label: 'Grau (entrada)' },
  { chave: 'grau_saida',     label: 'Grau (saída)' },
  { chave: 'pagerank',       label: 'PageRank' },
  { chave: 'autovetor',      label: 'Autovetor' },
  { chave: 'proximidade',    label: 'Proximidade' },
  { chave: 'intermediacao',  label: 'Intermediação' },
];

const TOP_N_OPCOES = [10, 25, 50];

@Component({
  selector: 'app-metricas',
  standalone: true,
  imports: [StatusView, RankingTable],
  templateUrl: './metricas.html',
})
export class Metricas implements OnInit {
  private route = inject(ActivatedRoute);
  repositorio = inject(Repositorio);

  analise = this.repositorio.analise;
  metricas = METRICAS;
  topNOpcoes = TOP_N_OPCOES;

  metricaSelecionada = signal<MetricaChave>('grau_entrada');
  topN = signal(10);

  ngOnInit() {
    const { owner, repo } = this.route.snapshot.params;
    const sel = this.repositorio.selecionado();
    if (!sel || sel.owner !== owner || sel.repo !== repo) {
      this.repositorio.selecionar(owner, repo);
    }
  }

  get errorMsg() {
    const e = this.analise.error() as any;
    if (!e) return null;
    return e?.message ?? e?.error?.detail ?? `HTTP ${e?.status ?? 'error'}`;
  }

  retry() {
    this.analise.reload();
  }

  rankingAtual = computed<ItemRanking[]>(() => {
    const a = this.analise.value();
    if (!a) return [];
    const chave = this.metricaSelecionada();
    const lista = a.centralidades?.[chave];
    if (!lista) return [];
    return lista.slice(0, this.topN());
  });

  metricaDisponivel(chave: MetricaChave): boolean {
    const a = this.analise.value();
    if (!a) return false;
    const lista = a.centralidades?.[chave];
    return Array.isArray(lista) && lista.length > 0;
  }

  coresComunidade = [
    'var(--data-1)', 'var(--data-2)', 'var(--data-3)', 'var(--data-4)',
    'var(--data-5)', 'var(--data-6)', 'var(--data-7)', 'var(--data-8)',
  ];

  corComunidade(idx: number) {
    return this.coresComunidade[idx % this.coresComunidade.length];
  }

  comunidadesEntries() {
    const a = this.analise.value();
    if (!a?.comunidades) return [];
    return Object.entries(a.comunidades);
  }

  pontesEntries() {
    const a = this.analise.value();
    if (!a?.pontes) return [];
    return Object.entries(a.pontes);
  }

  pontesLabel(chave: string) {
    const map: Record<string, string> = {
      locais:          'Pontes Locais',
      classicas:       'Pontes Clássicas',
      intercomunidade: 'Pontes Intercomunidade',
    };
    return map[chave] ?? chave;
  }

  formatarNum(v: number | null | undefined): string {
    if (v == null) return '—';
    if (Number.isInteger(v)) return v.toLocaleString('pt-BR');
    return v.toFixed(4);
  }
}
