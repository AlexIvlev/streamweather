from concurrent.futures import ProcessPoolExecutor
import os
import time
from functools import partial

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


def calculate_rolling_stats(data, window=30):
    """
    Вычисление скользящих статистик
    """
    rolling_mean = data['temperature'].rolling(window=window).mean()
    rolling_std = data['temperature'].rolling(window=window).std()
    return rolling_mean, rolling_std


def detect_anomalies(data, rolling_mean, rolling_std):
    """
    Обнаружение аномалий на основе скользящих статистик
    """
    upper_bound = rolling_mean + 2 * rolling_std
    lower_bound = rolling_mean - 2 * rolling_std
    anomalies = data[(data['temperature'] > upper_bound) |
                     (data['temperature'] < lower_bound)].copy()
    return anomalies, upper_bound, lower_bound


def analyze_long_term_trend(data):
    """
    Анализ долгосрочных трендов
    """
    data = data.copy()
    data['year'] = data['timestamp'].dt.year
    yearly_trends = data.groupby('year')['temperature'].agg(['mean', 'std']).reset_index()

    X = yearly_trends['year'].values.reshape(-1, 1)
    y = yearly_trends['mean'].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(X.flatten(), y)

    return yearly_trends, slope, r_value, p_value


def analyze_city_data(city_data):
    """
    Расширенный анализ данных по городу
    """
    # Базовая статистика
    descriptive_stats = city_data.select_dtypes(include=[np.number]).describe()

    # Вычисление скользящих статистик
    rolling_mean, rolling_std = calculate_rolling_stats(city_data)

    # Обнаружение аномалий
    anomalies, upper_bound, lower_bound = detect_anomalies(city_data, rolling_mean, rolling_std)

    # Анализ долгосрочных трендов
    yearly_trends, slope, r_value, p_value = analyze_long_term_trend(city_data)

    # Создание основного графика временного ряда
    temperature_plot = plt.figure(figsize=(12, 8))
    plt.plot(city_data['timestamp'], city_data['temperature'], label='Temperature', alpha=0.5)
    plt.plot(city_data['timestamp'], rolling_mean, label='30-day Moving Average', color='green')
    plt.fill_between(city_data['timestamp'],
                     upper_bound, lower_bound,
                     alpha=0.2, color='gray',
                     label='±2σ Range')
    plt.scatter(anomalies['timestamp'], anomalies['temperature'],
                color='red', label='Anomalies')
    plt.title('Temperature Time Series with Anomalies')
    plt.legend()

    # Создание сезонного графика
    city_data['month'] = city_data['timestamp'].dt.month
    seasonal_stats = city_data.groupby(['season', city_data['timestamp'].dt.year])['temperature'].agg([
        'mean', 'std', 'count'
    ]).reset_index()

    seasonal_plot = plt.figure(figsize=(10, 6))
    sns.boxplot(data=city_data, x='season', y='temperature')
    plt.title('Seasonal Temperature Distribution')

    # Создание графика долгосрочного тренда
    trend_plot = plt.figure(figsize=(10, 6))
    plt.plot(yearly_trends['year'], yearly_trends['mean'], marker='o')
    plt.fill_between(yearly_trends['year'],
                     yearly_trends['mean'] - yearly_trends['std'],
                     yearly_trends['mean'] + yearly_trends['std'],
                     alpha=0.2)
    plt.title(f'Long-term Trend (Slope: {slope:.3f}°C/year, R²: {r_value ** 2:.3f})')

    return descriptive_stats, temperature_plot, seasonal_plot, trend_plot, anomalies, slope, r_value, p_value, seasonal_stats


def analyze_all_cities(data, parallel=False):
    """
    Анализ данных для всех городов
    """
    cities = data['city'].unique()
    start_time = time.time()

    if parallel:
        # Используем partial для передачи данных в функцию
        with ProcessPoolExecutor() as executor:
            analyze_city_partial = partial(analyze_city_data_for_city, data)
            results = list(executor.map(analyze_city_partial, cities))
        # Преобразуем результаты в словарь для удобного доступа
        results_dict = dict(results)
    else:
        results_dict = {
            city: analyze_city_data(data[data['city'] == city])
            for city in cities
        }

    computation_time = time.time() - start_time
    return results_dict, computation_time


def analyze_city_data_for_city(data, city):
    """
    Анализ данных для одного города
    """
    print(f"Processing city: {city} in process {os.getpid()}")
    city_data = data[data['city'] == city]
    return city, analyze_city_data(city_data)
