# Dashboard Lego 🧱

Модульная библиотека для создания интерактивных дашбордов на Python с использованием Dash.

Dashboard Lego позволяет собирать сложные дашборды из независимых, переиспользуемых "блоков", как из конструктора. Это упрощает разработку, улучшает читаемость кода и способствует повторному использованию компонентов.

---

## ✨ Основные возможности

- **Модульная архитектура**: Собирайте дашборды из независимых блоков (KPI, графики, текст).
- **Реактивное состояние**: Встроенный менеджер состояний для легкого создания интерактивности между блоками (фильтры, drill-down и т.д.).
- **Гибкая сетка**: Располагайте блоки в любой конфигурации с помощью системы сеток на базе `dash-bootstrap-components`.
- **Кэширование данных**: Встроенный кэш на уровне источников данных для повышения производительности.
- **Простое расширение**: Легко создавайте собственные блоки и источники данных, наследуясь от базовых классов.

## 📦 Установка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/your-username/dashboard-lego.git
    cd dashboard-lego
    ```

2.  **Создайте виртуальное окружение и установите зависимости:**
    Рекомендуется использовать `uv` для быстрой установки.
    ```bash
    # Установка uv
    pip install uv

    # Создание окружения и установка зависимостей
    uv venv
    uv pip install -e .[dev]
    ```

## 🚀 Быстрый старт

Ниже приведен пример простого дашборда. Полный код можно найти в `examples/01_simple_dashboard.py`.

```python
# examples/01_simple_dashboard.py

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

from core.datasource import BaseDataSource
from core.page import DashboardPage
from blocks.kpi import KPIBlock
from blocks.chart import StaticChartBlock

# 1. Определите источник данных
class SalesDataSource(BaseDataSource):
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__()

    def _load_data(self, params: dict) -> pd.DataFrame:
        return pd.read_csv(self.file_path)

    def get_kpis(self) -> dict:
        if self._data is None: return {}
        return {
            "total_sales": self._data["Sales"].sum(),
            "total_units": self._data["UnitsSold"].sum()
        }
    # ... другие обязательные методы ...

# 2. Определите функцию для построения графика
def plot_sales_by_fruit(df: pd.DataFrame) -> go.Figure:
    sales_by_fruit = df.groupby("Fruit")["Sales"].sum().reset_index()
    return px.bar(sales_by_fruit, x="Fruit", y="Sales", title="Sales by Fruit")

# 3. Инициализируйте ваш источник данных и блоки
datasource = SalesDataSource(file_path="examples/sample_data.csv")
datasource.init_data()

kpi_block = KPIBlock(...)
chart_block = StaticChartBlock(...)

# 4. Соберите страницу дашборда
dashboard_page = DashboardPage(
    title="Simple Sales Dashboard",
    blocks=[
        [kpi_block],      # Первый ряд
        [chart_block]     # Второй ряд
    ]
)

# 5. Запустите приложение
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dashboard_page.build_layout()
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
```

Чтобы запустить этот пример, выполните:
```bash
python examples/01_simple_dashboard.py
```

## 🔗 Интерактивность

`dashboard-lego` позволяет легко связывать блоки между собой. Один блок может публиковать свое состояние (например, значение фильтра), а другие блоки могут подписываться на это состояние и обновляться соответствующим образом.

Это реализовано через `StateManager`, который автоматически создает Dash колбэки.

Полный пример интерактивного дашборда смотрите в `examples/02_interactive_dashboard.py`.

## 🎨 Пресеты

Пресеты — это готовые к использованию блоки для решения стандартных задач анализа данных (EDA), которые значительно сокращают количество шаблонного кода.

- **`CorrelationHeatmapPreset`**: Автоматически строит тепловую карту корреляций для всех числовых столбцов в ваших данных.
- **`GroupedHistogramPreset`**: Создает интерактивную гистограмму с выпадающими списками для выбора столбца и группировки.
- **`MissingValuesPreset`**: Отображает столбчатую диаграмму с процентом пропущенных значений для каждой колонки, что помогает быстро оценить качество данных.
- **`BoxPlotPreset`**: Позволяет сравнивать распределения числового признака по разным категориям с помощью интерактивных box plot диаграмм.

Пример использования пресетов можно найти в файле `examples/03_presets_dashboard.py`.

## 🧪 Тестирование

Библиотека покрыта юнит-тестами. Для запуска тестов:

```bash
# Убедитесь, что вы установили dev-зависимости
# uv pip install -e .[dev,docs,ml,sql]

# Запуск тестов
uv run pytest
```

## 🤝 Вклад в проект

Мы рады любому вкладу! Пожалуйста, ознакомьтесь с `CONTRIBUTING.md` для получения дополнительной информации.

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.