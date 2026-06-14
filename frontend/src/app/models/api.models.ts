export type EstadoRepositorio = 'disponivel' | 'ausente' | 'minerando' | 'erro';

export interface RepositorioResumo {
  nome: string;
  estado: EstadoRepositorio;
  quantidade_usuarios: number | null;
  quantidade_interacoes: number | null;
}

export type TipoGrafo = 'integrado' | 'comentarios' | 'fechamento' | 'prs';

export interface GrafoResumo {
  tipo: TipoGrafo;
  vertices: number;
  arestas: number;
  densidade: number;
}

export interface ItemRanking {
  username: string;
  valor: number;
}

export interface RelatorioAnalise {
  densidade: number;
  assortatividade: number;
  modularidade: number;
  centralidades: Record<string, ItemRanking[]>;
  comunidades: Record<string, string[]>;
  pontes: Record<string, [string, string][]>;
}

export interface JobMineracao {
  job_id: string;
  repo: string;
  estado: 'pendente' | 'executando' | 'concluido' | 'erro';
  detalhe: string | null;
}
