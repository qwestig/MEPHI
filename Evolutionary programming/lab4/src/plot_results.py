"""Coverage curves, per-run quality and per-branch repeatability."""
from collections import defaultdict
import csv
import os
from pathlib import Path
import statistics
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'lab34-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'
LABELS={'random_search':'Случайный поиск','coverage_ga':'ГА с редкостью ветвей','directed_ga':'Направленный ГА'}
COLORS=['#657caa','#db8c24','#21866c']


def rows(name):
    with (OUT/name).open() as f:
        return list(csv.DictReader(f))


def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
    def save(fig,name):
        for ext in ['png','svg']:
            fig.savefig(OUT/f'{name}.{ext}',dpi=160,bbox_inches='tight')
        plt.close(fig)
    grouped=defaultdict(list)
    for r in rows('trajectories.csv'):
        grouped[r['method'],int(r['evaluations'])].append(100*int(r['covered'])/int(r['total']))
    fig,ax=plt.subplots(figsize=(10,5.5),layout='constrained')
    for method,color in zip(LABELS,COLORS):
        xs=sorted(n for m,n in grouped if m==method)
        ys=[grouped[method,n] for n in xs]
        ax.plot(xs,[statistics.fmean(v) for v in ys],label=LABELS[method],color=color,lw=2)
        ax.fill_between(xs,[min(v) for v in ys],[max(v) for v in ys],color=color,alpha=.10)
    ax.set(title='Покрытие ветвей: среднее и диапазон 30 запусков',xlabel='Исполнения функции',ylabel='Покрыто ветвей, %',ylim=(40,102))
    ax.legend(); ax.grid(alpha=.2)
    save(fig,'convergence')
    runs=rows('runs.csv')
    fig,ax=plt.subplots(figsize=(9,5.5),layout='constrained')
    data=[[100*float(r['coverage']) for r in runs if r['method']==m] for m in LABELS]
    ax.boxplot(data,tick_labels=['Случайный поиск','ГА с редкостью\nветвей','Направленный ГА'])
    for i,values in enumerate(data):
        ax.scatter([i+1+(j%5-2)*.035 for j in range(len(values))],values,s=18,color=COLORS[i],alpha=.7)
    ax.set(title='Итоговое покрытие при одинаковом бюджете',ylabel='Покрыто ветвей, %',ylim=(50,102))
    ax.grid(axis='y',alpha=.2)
    save(fig,'quality')
    rates=rows('branch_rates.csv')
    branches=[r['branch'] for r in rates if r['method']=='random_search']
    fig,ax=plt.subplots(figsize=(16,4.5),layout='constrained')
    matrix=[[100*int(next(r['covered_runs'] for r in rates if r['method']==m and r['branch']==b))/30 for b in branches] for m in LABELS]
    im=ax.imshow(matrix,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(len(branches)),[b.replace('admission','A').replace('shipping','S').replace('order','O') for b in branches],rotation=90,fontsize=8)
    ax.set_yticks(range(3),list(LABELS.values()))
    ax.set(title='Повторяемость покрытия каждой ветви по 30 запускам',xlabel='O — order, S — shipping, A — admission; T/F — исход условия')
    fig.colorbar(im,ax=ax,label='Запуски, покрывшие ветвь, %',shrink=.8)
    save(fig,'branch_coverage')
    print('lab4: figures saved',flush=True)


if __name__=='__main__':
    main()
