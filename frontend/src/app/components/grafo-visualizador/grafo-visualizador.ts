import {
  Component,
  DestroyRef,
  ElementRef,
  effect,
  inject,
  input,
  viewChild,
} from '@angular/core';
import { DataSet } from 'vis-data';
import { Network } from 'vis-network';
import type { Edge, Node, Options } from 'vis-network';
import { GrafoVisualizacao } from '../../models/api.models';

/**
 * Renderiza um grafo dirigido e ponderado com vis.js (vis-network).
 *
 * As cores são lidas dos design tokens (CSS custom properties) na hora do render,
 * então o grafo acompanha o tema (claro/escuro) atual. O componente vive dentro do
 * `@if` do modal: é criado ao abrir e destruído ao fechar, então o ciclo de vida da
 * `Network` é simples (criar no `effect`, destruir no `DestroyRef`).
 */
@Component({
  selector: 'app-grafo-visualizador',
  standalone: true,
  template: `
    <div
      #container
      class="w-full h-[60vh] rounded-[6px] nb-border"
      style="background: var(--bg)"
    ></div>
  `,
})
export class GrafoVisualizador {
  dados = input.required<GrafoVisualizacao>();

  private container = viewChild<ElementRef<HTMLDivElement>>('container');
  private network: Network | null = null;

  constructor() {
    effect(() => {
      const ref = this.container();
      if (!ref) return;
      this.render(ref.nativeElement, this.dados());
    });

    inject(DestroyRef).onDestroy(() => this.network?.destroy());
  }

  private render(el: HTMLDivElement, dados: GrafoVisualizacao): void {
    this.network?.destroy();

    const css = getComputedStyle(document.documentElement);
    const token = (nome: string, padrao: string) => css.getPropertyValue(nome).trim() || padrao;
    const primary = token('--primary', '#4f46e5');
    const ink = token('--ink', '#111111');
    const fg = token('--fg', '#111111');
    const muted = token('--muted', '#888888');

    const nodes = new DataSet<Node>(
      dados.nos.map((n) => ({
        id: n.id,
        label: n.id,
        title: `${n.id} — entrada: ${n.grau_entrada}, saída: ${n.grau_saida}`,
        value: n.grau_entrada + n.grau_saida,
      }))
    );
    const edges = new DataSet<Edge>(
      dados.arestas.map((a, i) => ({
        id: i,
        from: a.origem,
        to: a.destino,
        value: a.peso,
        title: `peso: ${a.peso}`,
      }))
    );

    const opcoes: Options = {
      autoResize: true,
      nodes: {
        shape: 'dot',
        scaling: { min: 8, max: 34, label: { enabled: true, min: 12, max: 26 } },
        color: { background: primary, border: ink, highlight: { background: primary, border: ink } },
        font: { color: fg, face: 'Space Grotesk, sans-serif', size: 14 },
        borderWidth: 2,
      },
      edges: {
        arrows: { to: { enabled: true, scaleFactor: 0.6 } },
        color: { color: muted, highlight: ink },
        scaling: { min: 1, max: 6 },
        smooth: { enabled: true, type: 'continuous', roundness: 0.5 },
      },
      physics: {
        stabilization: { enabled: true, iterations: 200 },
        barnesHut: { gravitationalConstant: -8000, springLength: 120, avoidOverlap: 0.2 },
      },
      interaction: { hideEdgesOnDrag: true, tooltipDelay: 120 },
    };

    this.network = new Network(el, { nodes, edges }, opcoes);
    // Desliga a física após estabilizar para não consumir CPU com o modal aberto.
    this.network.once('stabilizationIterationsDone', () =>
      this.network?.setOptions({ physics: false })
    );
  }
}
