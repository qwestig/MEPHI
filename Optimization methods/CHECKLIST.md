# Соответствие требованиям

Вариант 13, N=7, Б24-517, осень 2026. Этот список фиксирует материалы; окончательную оценку и допуск определяет преподаватель на защите.

| Требование | Где выполнено |
| --- | --- |
| Три обязательные ЛР | reports/lab1.md, lab2.md, lab3.md; разделы единого PDF |
| Вариант и seed | data/variant.json, начало каждого отчёта |
| Масштаб ЛР 1: 6 филиалов, 3 вида ограничений | data/lab1.json; src/lab1.py |
| Масштаб ЛР 2: 3 склада, 4 магазина, 4 периода | data/lab2.json; src/lab2.py |
| Масштаб ЛР 3: 5 поставщиков, 4 товара | data/lab3.json; src/lab3.py |
| Множества, параметры, переменные, цель, ограничения, единицы | Разделы формальных моделей всех трёх отчётов |
| Данные отдельно от кода, генерация и один запуск | data/; src/data.py; python main.py --generate |
| Открытый HiGHS и реальные логи | highspy; results/lab*/logs/*.log |
| Независимая проверка и цель, допуск 1e-7 | src/verify.py; results/lab*/checks.json; check_results.py |
| Фиксация версий | requirements.txt, requirements-lock.txt, .python-version, environment.json |
| Статусы и пределы их интерпретации | Каждый отчёт, README.md |
| ЛР 1: база, ресурс -20%, двойной стресс | results/lab1/scenarios.csv; сценарные планы |
| ЛР 1: цены активных ограничений, прогноз и факт | constraints.csv; shadow_prediction.csv |
| ЛР 1: объяснение нулевых переменных | reduced_costs.csv; отчёт |
| ЛР 2: схема потоков и ёмкостей | Четыре графа и график запасов; solution_base.csv |
| ЛР 2: баланс каждой вершины и границы дуг | balances.csv, проверки NumPy |
| ЛР 2: перегрузка, отказ, спрос +20% | scenarios.csv; diagnostics.json; elastic_plan_*.json |
| ЛР 2: насыщенные дуги и цены | bottlenecks.csv; односторонние перерешивания |
| ЛР 2: жадная эвристика и зазор | greedy.json; greedy_solution.csv |
| ЛР 3: LP-релаксация, оба решения и интегральный gap | solution_lp.csv; lp_plan.json; solution_base.csv |
| ЛР 3: все связки, целочисленность и пересчёт цели | verify.purchasing; checks.json |
| ЛР 3: три сценария, состав поставщиков | scenarios.csv; solution_*.csv |
| ЛР 3: время и gap при росте масштаба | benchmark.csv, benchmark_raw.csv, figures/benchmark.png |
| ЛР 3: жадная эвристика, стоимость и время | greedy.json; greedy_solution.csv |
| ЛР 3: обоснованное и избыточное M | Сильная и слабая модели, paired benchmark |
| Звёздочка 10: полная двойственная задача | reports/star10_duality.md; dual_solution.csv; dual_certificate.json |
| Звёздочка 6: две эквивалентные MILP, LP и ветвление | reports/star6_formulations.md; benchmark*; все логи |
| Практические ограничения моделей | Вывод каждой ЛР |
| Подготовка к защите | reports/defense.md; 15 вопросов |

Методичка упоминает допуск к ЛР 4, но содержит задания только ЛР 1-3. Для уровня A явно указаны ЛР 1-3 и не менее двух заданий со звёздочкой; несуществующая в PDF ЛР 4 в комплект не добавлялась.
