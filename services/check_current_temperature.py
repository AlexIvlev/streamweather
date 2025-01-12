from datetime import datetime


def get_current_season():
    """
    Определяем текущий сезон на основе текущей даты
    """
    month = datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'


def check_current_temperature(current_temp, city_data):
    """
    Анализ текущей температуры на основе исторических данных
    """
    # Получаем текущий сезон на основе даты
    current_season = get_current_season()

    # Фильтруем данные по текущему сезону
    seasonal_data = city_data[city_data['season'] == current_season]

    # Проверяем, есть ли данные для текущего сезона
    if seasonal_data.empty:
        return {
            'error': f'Нет исторических данных для сезона {current_season}'
        }

    # Базовые статистики для сезона
    mean_temp = seasonal_data['temperature'].mean()
    std_temp = seasonal_data['temperature'].std()

    # Проверяем, является ли температура аномальной
    is_anomaly = abs(current_temp - mean_temp) > 2 * std_temp

    return {
        'season': current_season,
        'mean_temp': mean_temp,
        'is_anomaly': is_anomaly,
        'difference': current_temp - mean_temp
    }
