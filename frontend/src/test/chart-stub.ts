import { Directive, input, type Type } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ChartOptions, Plugin } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import type { LineData } from '../utils/lineChart';

@Directive({ selector: 'canvas[baseChart]' })
export class ChartStub {
  readonly type = input<'line'>();
  readonly data = input.required<LineData>();
  readonly options = input<ChartOptions<'line'>>();
  readonly plugins = input<Plugin<'line'>[]>([]);
}

export function stubChart(...components: Type<unknown>[]): void {
  for (const component of components) {
    TestBed.overrideComponent(component, {
      remove: { imports: [BaseChartDirective] },
      add: { imports: [ChartStub] }
    });
  }
}
