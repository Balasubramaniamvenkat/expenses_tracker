import { ChartConfiguration, ChartData, ChartOptions, ChartType } from 'chart.js';

export interface ChartConfig {
  type: ChartType;
  data: ChartData;
  options: ChartOptions;
  responsive: boolean;
  maintainAspectRatio: boolean;
}

export interface DonutChartConfig extends ChartConfig {
  type: 'doughnut';
}

export interface PieChartConfig extends ChartConfig {
  type: 'pie';
}

export interface BarChartConfig extends ChartConfig {
  type: 'bar';
}

export interface LineChartConfig extends ChartConfig {
  type: 'line';
}

export interface SunburstData {
  name: string;
  value: number;
  children?: SunburstData[];
  color?: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  color: string;
  displayValue: number;
  formattedValue: string;
  tooltipText: string;
}

export interface MobileChartConfig {
  maintainAspectRatio: boolean;
  aspectRatio: number;
  plugins: {
    legend: {
      position: 'bottom' | 'top' | 'left' | 'right';
      labels: {
        boxWidth: number;
        fontSize: number;
      };
    };
  };
  elements: {
    point: { radius: number };
    line: { borderWidth: number };
  };
}
