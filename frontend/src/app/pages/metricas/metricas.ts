import { Component, computed, HostListener, inject, OnInit, signal, ViewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CdkVirtualScrollViewport, ScrollingModule } from '@angular/cdk/scrolling';
import { LucideAngularModule } from 'lucide-angular';
import { Repositorio } from '../../services/repositorio';
import { StatusView } from '../../components/status-view/status-view';
import { RankingTable } from '../../components/ranking-table/ranking-table';
import { Modal } from '../../components/modal/modal';
import { InfoHint } from '../../components/info-hint/info-hint';
import { Tooltip } from '../../components/tooltip/tooltip';
import { ItemRanking, TipoGrafo } from '../../models/api.models';

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

const TIPOS_VALIDOS = new Set<TipoGrafo>(['integrado', 'comentarios', 'fechamento', 'prs']);

const TIPO_LABEL: Record<TipoGrafo, string> = {
  integrado:   'Integrado',
  comentarios: 'Comentários',
  fechamento:  'Fechamento',
  prs:         'Pull Requests',
};

// Resumos curtos por métrica/seção, exibidos no tooltip do ícone "i".
const DESCRICOES: Record<string, string> = {
  densidade: 'Proporção de arestas existentes em relação ao total possível (0 a 1). Mais alta = rede mais conectada.',
  clustering: 'Coeficiente de aglomeração: o quanto os vizinhos de um usuário também interagem entre si, na média.',
  assortatividade: 'Assortatividade: mostra se colaboradores com muitas conexões tendem a se conectar entre si (rede centralizada) ou se interagem mais com colaboradores menos conectados.',
  modularidade: 'Qualidade da divisão em comunidades (−0,5 a 1). Mais alta = comunidades mais bem definidas.',
  grau_entrada: 'Quantidade de interações recebidas por usuário (normalizada).',
  grau_saida: 'Quantidade de interações enviadas por usuário (normalizada).',
  pagerank: 'Importância de um usuário considerando a importância de quem interage com ele.',
  autovetor: 'Centralidade de autovetor: influência ponderada pela importância dos vizinhos.',
  proximidade: 'Quão perto, em média, um usuário está dos demais pela rede de interações.',
  intermediacao: 'O quanto um usuário está nos caminhos mais curtos entre os outros (papel de ponte).',
  comunidades: 'Grupos de usuários que interagem mais entre si, detectados pelo algoritmo de Louvain.',
  locais: 'Pares de usuários conectados que não compartilham vizinhos em comum (conexões "frágeis").',
  classicas: 'Arestas cuja remoção desconecta partes do grafo (pontes no sentido clássico).',
  intercomunidade: 'Arestas que ligam usuários de comunidades diferentes.',
};

@Component({
  selector: 'app-metricas',
  standalone: true,
  imports: [StatusView, RankingTable, Modal, InfoHint, Tooltip, ScrollingModule, RouterLink, LucideAngularModule],
  templateUrl: './metricas.html',
})
export class Metricas implements OnInit {
  private route = inject(ActivatedRoute);
  repositorio = inject(Repositorio);
  @ViewChild('comunidadeViewport') private comunidadeViewport?: CdkVirtualScrollViewport;

  analise = this.repositorio.analise;
  metricas = METRICAS;
  topNOpcoes = TOP_N_OPCOES;
  descricoes = DESCRICOES;

  metricaSelecionada = signal<MetricaChave>('grau_entrada');
  topN = signal(10);
  topArestas = signal(10);

  // Botão "voltar ao topo" (aparece após rolar a página).
  mostrarTopo = signal(false);

  // Modal de drill-down de comunidade.
  comunidadeAberta = signal<{ titulo: string; usuarios: string[] } | null>(null);

  @HostListener('window:scroll')
  onScroll() {
    this.mostrarTopo.set(window.scrollY > 400);
  }

  @HostListener('window:resize')
  onResize() {
    if (this.comunidadeAberta()) this.atualizarViewportComunidade(false);
  }

  voltarAoTopo() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /** Altura do viewport virtual: cabe no conteúdo, com teto (evita espaço em branco). */
  alturaLista(n: number, itemSize: number, max: number): number {
    return Math.min(n * itemSize, max);
  }

  alturaModalComunidade(n: number): number {
    const limiteTela = typeof window === 'undefined' ? 420 : Math.max(200, window.innerHeight - 220);
    return Math.min(n * 40, Math.min(520, limiteTela));
  }

  metricaLabelAtual = computed(
    () => METRICAS.find(m => m.chave === this.metricaSelecionada())?.label ?? ''
  );

  constructor() {
    // O componente é reusado entre /metricas/:tipo, então reagimos a cada troca de param.
    this.route.paramMap.pipe(takeUntilDestroyed()).subscribe(pm => {
      const owner = pm.get('owner')!;
      const repo = pm.get('repo')!;
      const tipo = (pm.get('tipo') ?? 'integrado') as TipoGrafo;
      this.repositorio.tipoAnalise.set(TIPOS_VALIDOS.has(tipo) ? tipo : 'integrado');
      const sel = this.repositorio.selecionado();
      if (!sel || sel.owner !== owner || sel.repo !== repo) {
        this.repositorio.selecionar(owner, repo);
      }
    });
  }

  ngOnInit() {}

  tipoAtual = computed(() => this.repositorio.tipoAnalise());
  tipoLabel = computed(() => TIPO_LABEL[this.tipoAtual()] ?? this.tipoAtual());

  get errorMsg() {
    const e = this.analise.error() as any;
    if (!e) return null;
    return e?.message ?? e?.error?.detail ?? `HTTP ${e?.status ?? 'error'}`;
  }

  retry() {
    this.analise.reload();
  }

  graus = computed(() => this.analise.value()?.graus ?? {});

  rankingAtual = computed<ItemRanking[]>(() => {
    const a = this.analise.value();
    if (!a) return [];
    const chave = this.metricaSelecionada();
    const lista = a.centralidades?.[chave];
    if (!lista) return [];
    return lista.slice(0, this.topN());
  });

  arestasMaisPesadas = computed(() => {
    const arestas = this.analise.value()?.arestas_mais_pesadas ?? [];
    return arestas.slice(0, this.topArestas());
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

  abrirComunidade(idx: number, usuarios: string[]) {
    this.comunidadeAberta.set({ titulo: `Comunidade ${idx + 1}`, usuarios });
    this.atualizarViewportComunidade();
  }

  trackUsuario(index: number, usuario: string) {
    return `${index}:${usuario}`;
  }

  private atualizarViewportComunidade(resetarScroll = true) {
    if (typeof requestAnimationFrame === 'undefined') return;
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const viewport = this.comunidadeViewport;
        if (!viewport) return;
        if (resetarScroll) viewport.scrollToIndex(0);
        viewport.checkViewportSize();
      });
    });
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
      intercomunidade: 'Arestas Intercomunidade',
    };
    return map[chave] ?? chave;
  }

  formatarNum(v: number | null | undefined): string {
    if (v == null) return '—';
    if (Number.isInteger(v)) return v.toLocaleString('pt-BR');
    return v.toFixed(4);
  }
}
