import { Injectable } from '@angular/core';
import { CategoryAnalytics } from '../models/category.model';
import { ChartDataPoint, SunburstData } from '../models/chart-config.model';

@Injectable({
  providedIn: 'root'
})
export class ChartDataService {

  generateDonutConfig(analytics: CategoryAnalytics[], displayMode: 'amount' | 'percentage'): any {
    const isAmountMode = displayMode === 'amount';
    
    return {
      type: 'doughnut',
      data: {
        labels: analytics.map(a => a.categoryName),
        datasets: [{
          data: isAmountMode 
            ? analytics.map(a => a.monthlyAmount)
            : analytics.map(a => a.percentageOfIncome),
          backgroundColor: analytics.map(a => a.color),
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverBorderWidth: 3,
          hoverBorderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '50%',
        plugins: {
          legend: { 
            position: 'bottom',
            labels: {
              usePointStyle: true,
              padding: 20,
              font: {
                size: 12
              }
            }
          },
          tooltip: { 
            callbacks: {
              label: (context: any) => this.formatTooltip(context, displayMode, analytics[context.dataIndex])
            },
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderColor: '#ffffff',
            borderWidth: 1
          }
        },
        animation: {
          duration: 1000
        }
      }
    };
  }

  generatePieConfig(analytics: CategoryAnalytics[], displayMode: 'amount' | 'percentage'): any {
    const isAmountMode = displayMode === 'amount';
    
    return {
      type: 'pie',
      data: {
        labels: analytics.map(a => a.categoryName),
        datasets: [{
          data: isAmountMode 
            ? analytics.map(a => a.monthlyAmount)
            : analytics.map(a => a.percentageOfIncome),
          backgroundColor: analytics.map(a => a.color),
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            position: 'bottom',
            labels: {
              usePointStyle: true,
              padding: 20
            }
          },
          tooltip: { 
            callbacks: {
              label: (context: any) => this.formatTooltip(context, displayMode, analytics[context.dataIndex])
            }
          }
        }
      }
    };
  }

  generateBarConfig(analytics: CategoryAnalytics[], displayMode: 'amount' | 'percentage'): any {
    const isAmountMode = displayMode === 'amount';
    
    return {
      type: 'bar',
      data: {
        labels: analytics.map(a => a.categoryName),
        datasets: [{
          label: isAmountMode ? 'Amount (₹)' : 'Percentage (%)',
          data: isAmountMode 
            ? analytics.map(a => a.monthlyAmount)
            : analytics.map(a => a.percentageOfIncome),
          backgroundColor: analytics.map(a => a.color),
          borderColor: analytics.map(a => a.color),
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value: any) => isAmountMode 
                ? `₹${Number(value).toLocaleString()}`
                : `${value}%`
            }
          }
        },
        plugins: {
          legend: { 
            display: false
          },
          tooltip: { 
            callbacks: {
              label: (context: any) => this.formatTooltip(context, displayMode, analytics[context.dataIndex])
            }
          }
        }
      }
    };
  }

  generateLineConfig(analytics: CategoryAnalytics[], displayMode: 'amount' | 'percentage'): any {
    const isAmountMode = displayMode === 'amount';
    
    return {
      type: 'line',
      data: {
        labels: analytics.map(a => a.categoryName),
        datasets: [{
          label: isAmountMode ? 'Amount (₹)' : 'Percentage (%)',
          data: isAmountMode 
            ? analytics.map(a => a.monthlyAmount)
            : analytics.map(a => a.percentageOfIncome),
          borderColor: '#2196F3',
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: analytics.map(a => a.color),
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 6,
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value: any) => isAmountMode 
                ? `₹${Number(value).toLocaleString()}`
                : `${value}%`
            }
          }
        },
        plugins: {
          legend: { 
            display: false
          },
          tooltip: { 
            callbacks: {
              label: (context: any) => this.formatTooltip(context, displayMode, analytics[context.dataIndex])
            }
          }
        }
      }
    };
  }

  getChartConfigForMode(
    analytics: CategoryAnalytics[], 
    chartType: string, 
    displayMode: 'amount' | 'percentage'
  ): any {
    switch (chartType) {
      case 'donut':
        return this.generateDonutConfig(analytics, displayMode);
      case 'pie':
        return this.generatePieConfig(analytics, displayMode);
      case 'bar':
        return this.generateBarConfig(analytics, displayMode);
      case 'line':
        return this.generateLineConfig(analytics, displayMode);
      case 'sunburst':
        return this.generateDonutConfig(analytics, displayMode);
      default:
        return this.generateDonutConfig(analytics, displayMode);
    }
  }

  formatTooltip(context: any, displayMode: 'amount' | 'percentage', category?: CategoryAnalytics): string {
    const value = context.parsed;
    if (displayMode === 'amount') {
      const formatted = `₹${Number(value).toLocaleString()}`;
      return `${context.label}: ${formatted}`;
    } else {
      return `${context.label}: ${Number(value).toFixed(1)}%`;
    }
  }

  generateChartDataPoints(analytics: CategoryAnalytics[], displayMode: 'amount' | 'percentage'): ChartDataPoint[] {
    return analytics.map(category => ({
      label: category.categoryName,
      value: displayMode === 'amount' ? category.monthlyAmount : category.percentageOfIncome,
      color: category.color,
      displayValue: displayMode === 'amount' 
        ? category.monthlyAmount 
        : category.percentageOfIncome,
      formattedValue: displayMode === 'amount'
        ? `₹${category.monthlyAmount.toLocaleString()}`
        : `${category.percentageOfIncome.toFixed(1)}%`,
      tooltipText: displayMode === 'amount'
        ? `Monthly Average: ₹${category.monthlyAmount.toLocaleString()}`
        : `${category.percentageOfIncome.toFixed(1)}% of total income`
    }));
  }

  generateSunburstData(analytics: CategoryAnalytics[]): SunburstData {
    return {
      name: 'Categories',
      value: analytics.reduce((sum, cat) => sum + cat.monthlyAmount, 0),
      children: analytics.map(category => ({
        name: category.categoryName,
        value: category.monthlyAmount,
        color: category.color,
        children: category.subcategories.map(sub => ({
          name: sub.name,
          value: sub.amount,
          color: category.color
        }))
      }))
    };
  }

  getMobileChartConfig(): any {
    return {
      maintainAspectRatio: false,
      aspectRatio: 1,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { 
            boxWidth: 12, 
            font: { size: 10 }
          }
        }
      },
      elements: {
        point: { radius: 3 },
        line: { borderWidth: 2 }
      }
    };
  }
}
