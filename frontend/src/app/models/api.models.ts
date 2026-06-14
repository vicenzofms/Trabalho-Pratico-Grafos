export type EstadoRepositorio = 'disponivel' | 'ausente' | 'minerando' | 'erro';

export interface RepositorioResumo {
  nome: string;
  estado: EstadoRepositorio;
  quantidade_usuarios: number | null;
  quantidade_interacoes: number | null;
}

export type TipoGrafo = 'integrado' | 'comentarios' | 'fechamento' | 'prs';

export type TipoRepresentacao = 'matriz' | 'lista';

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

export interface GrauUsuario {
  entrada: number;
  saida: number;
}

export interface ItemArestaPeso {
  origem: string;
  destino: string;
  peso: number;
}

export interface RelatorioAnalise {
  densidade: number | null;
  clustering: number | null;
  assortatividade: number | null;
  modularidade: number | null;
  centralidades: Record<string, ItemRanking[]>;
  graus: Record<string, GrauUsuario>;
  arestas_mais_pesadas: ItemArestaPeso[];
  comunidades: Record<string, string[]>;
  pontes: Record<string, [string, string][]>;
}

export interface JobMineracao {
  job_id: string;
  repo: string;
  estado: 'pendente' | 'executando' | 'concluido' | 'erro';
  detalhe: string | null;
}
