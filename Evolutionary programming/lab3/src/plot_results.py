"""Static Pareto projections and aggregate performance figures."""
from collections import defaultdict
import csv
import json
import os
from pathlib import Path
import statistics
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'lab34-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results'
LABELS = {'nsga2':'NSGA-II', 'weighted_sum':'Взвешенная сумма', 'random_search':'Случайный поиск'}
COLORS = ['#21866c','#db8c24','#657caa']


def rows(name):
    with (OUT/name).open() as f:
        return list(csv.DictReader(f))


def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
    reference = json.loads((OUT/'reference_front.json').read_text())
    fronts = json.loads((OUT/'fronts.json').read_text())
    runs = rows('runs.csv')
    def save(fig, name):
        for ext in ['png','svg']:
            fig.savefig(OUT/f'{name}.{ext}', dpi=160, bbox_inches='tight')
        plt.close(fig)
    fig, axes = plt.subplots(3,3,figsize=(15,12),layout='constrained')
    names = ['Стоимость, у.е.', 'Мощность, Вт', 'Производительность, баллы']
    exact = [row['objectives'] for row in reference['solutions']]
    def coordinates(values,k):
        return [(-v[k] if k==2 else v[k]) for v in values]
    for row_index,(method,color) in enumerate(zip(LABELS,COLORS)):
        chosen=max((r for r in runs if r['method']==method),key=lambda r:float(r['hv_ratio']))
        values=[r['objectives'] for r in fronts if r['method']==method and r['run']==int(chosen['run'])]
        for ax,(i,j) in zip(axes[row_index],[(0,1),(0,2),(1,2)]):
            ax.scatter(coordinates(exact,i),coordinates(exact,j),s=18,c='#d0d5da',label='Точный фронт')
            ax.scatter(coordinates(values,i),coordinates(values,j),s=9,alpha=.8,c=color,label=LABELS[method])
            ax.set(xlabel=names[i],ylabel=names[j],title=LABELS[method])
            ax.grid(alpha=.2)
        axes[row_index,0].legend(fontsize=8)
    fig.suptitle('Проекции лучшего по HV запуска каждого метода и точного фронта',fontsize=14)
    save(fig,'pareto')
    grouped=defaultdict(list)
    for r in rows('trajectories.csv'):
        grouped[r['method'],int(r['evaluations'])].append(float(r['hypervolume'])/reference['hypervolume']*100)
    fig,ax=plt.subplots(figsize=(10,5.5),layout='constrained')
    for method,color in zip(LABELS,COLORS):
        xs=sorted(n for m,n in grouped if m==method)
        ys=[grouped[method,n] for n in xs]
        ax.plot(xs,[statistics.fmean(v) for v in ys],c=color,lw=2,label=LABELS[method])
        ax.fill_between(xs,[min(v) for v in ys],[max(v) for v in ys],color=color,alpha=.12)
    ax.set(xlabel='Оценки целевой функции',ylabel='HV / HV точного фронта, %',title='Сходимость: среднее и диапазон 20 запусков')
    ax.legend(); ax.grid(alpha=.2)
    save(fig,'convergence')
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,key,title in zip(axes,['hv_ratio','exact_recall'],['Доля гиперобъёма','Доля решений точного фронта']):
        data=[[100*float(r[key]) for r in runs if r['method']==m] for m in LABELS]
        ax.boxplot(data,tick_labels=['NSGA-II','Взвешенная\nсумма','Случайный\nпоиск'])
        for i,values in enumerate(data):
            ax.scatter([i+1+(j%5-2)*.035 for j in range(len(values))],values,s=15,c=COLORS[i],alpha=.7)
        ax.set(title=title,ylabel='%'); ax.grid(axis='y',alpha=.2)
    save(fig,'quality')
    print('lab3: figures saved',flush=True)


if __name__=='__main__':
    main()
