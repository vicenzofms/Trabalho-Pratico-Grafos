import { Component, computed, input } from '@angular/core';
import { GrauUsuario, ItemRanking } from '../../models/api.models';
import { Tooltip } from '../tooltip/tooltip';

@Component({
  selector: 'app-ranking-table',
  standalone: true,
  imports: [Tooltip],
  template: `
    <div class="nb-border-3 nb-shadow rounded-[6px] overflow-hidden bg-surface">
      <table class="w-full" role="table">
        <thead>
          <tr class="border-b-[3px] border-ink">
            <th class="text-left px-4 py-3 font-bold text-sm w-12">#</th>
            <th class="text-left px-4 py-3 font-bold text-sm">Usuário</th>
            @if (mostrarGraus()) {
              <th class="text-right px-3 py-3 font-bold text-sm hidden sm:table-cell">
                <app-tooltip texto="Grau de entrada (arestas recebidas)">
                  <span>Grau ent.</span>
                </app-tooltip>
              </th>
              <th class="text-right px-3 py-3 font-bold text-sm hidden sm:table-cell">
                <app-tooltip texto="Grau de saída (arestas enviadas)">
                  <span>Grau saí.</span>
                </app-tooltip>
              </th>
            }
            <th class="text-right px-4 py-3 font-bold text-sm" aria-sort="descending">Valor</th>
          </tr>
        </thead>
        <tbody>
          @for (item of items(); track item.username; let i = $index) {
            <tr
              class="border-b border-ink/20 hover:bg-muted/10 transition-colors"
              [style.animation-delay.ms]="i * 40"
              style="animation: fadeInUp 0.3s ease-out both"
            >
              <td class="px-4 py-3 font-mono text-sm text-muted">{{ i + 1 }}</td>
              <td class="px-4 py-3 font-semibold">{{ item.username }}</td>
              @if (mostrarGraus()) {
                <td class="px-3 py-3 text-right font-mono tabular-nums text-sm text-muted hidden sm:table-cell">
                  {{ grau(item.username)?.entrada ?? '—' }}
                </td>
                <td class="px-3 py-3 text-right font-mono tabular-nums text-sm text-muted hidden sm:table-cell">
                  {{ grau(item.username)?.saida ?? '—' }}
                </td>
              }
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-2">
                  <div class="relative h-2 w-24 bg-muted/20 nb-border rounded-full overflow-hidden hidden sm:block">
                    <div
                      class="absolute inset-y-0 left-0 bg-tertiary"
                      [style.width.%]="(item.valor / maxValor()) * 100"
                    ></div>
                  </div>
                  <span class="font-mono tabular-nums text-sm">{{ formatarValor(item.valor) }}</span>
                </div>
              </td>
            </tr>
          }
        </tbody>
      </table>
    </div>

    <style>
      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
    </style>
  `,
})
export class RankingTable {
  items = input<ItemRanking[]>([]);
  topN = input(10);
  graus = input<Record<string, GrauUsuario>>({});

  mostrarGraus = computed(() => Object.keys(this.graus()).length > 0);

  grau(username: string): GrauUsuario | undefined {
    return this.graus()[username];
  }

  maxValor() {
    const list = this.items();
    return list.length ? Math.max(...list.map(i => i.valor)) : 1;
  }

  formatarValor(v: number) {
    if (v === 0) return '0';
    if (Math.abs(v) < 0.001) return v.toExponential(3);
    if (Number.isInteger(v)) return v.toLocaleString('pt-BR');
    return v.toFixed(4);
  }
}
