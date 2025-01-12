import io

import streamlit as st
import pandas as pd

from services import generate_realistic_temperature_data, seasonal_temperatures, get_current_weather, analyze_city_data, \
    analyze_all_cities, check_current_temperature
from translations import translations

# Страница приложения
st.set_page_config(page_title="Streamweather", layout="wide")

# Выбор языка
language = st.sidebar.selectbox("Choose language", ["ru", "en"])

# Получение переводов для выбранного языка
trans = translations.get(language, translations["ru"])

st.title(trans["title"])


@st.cache_data
def load_data(file):
    """Функция для загрузки данных"""
    return pd.read_csv(file)


weather_container = st.container()

# Кнопка для генерации и скачивания данных
generate_button = st.sidebar.button(trans["generate_data"])
if generate_button:
    # Генерация данных
    data = generate_realistic_temperature_data(list(seasonal_temperatures.keys()))

    # Сохранение данных в память (в формате CSV)
    csv_buffer = io.BytesIO()
    data.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)

    st.success(trans["file_generated"])

    # Создание кнопки для скачивания
    st.download_button(
        label=trans["download_csv"],
        data=csv_buffer,
        file_name="temperature_data.csv",
        mime="text/csv"
    )


# Интерфейс для загрузки файла с историческими данными
historical_file = st.sidebar.file_uploader(trans["upload_file"], type=["csv"])

# Инициализируем атрибуты в session_state, если они еще не существуют
if "results_cache" not in st.session_state:
    st.session_state.results_cache = {}

if "historical_file" not in st.session_state:
    st.session_state.historical_file = None

# Проверяем, был ли загружен новый файл
if historical_file is not None:
    # Если файл новый, очищаем кэш
    if st.session_state.historical_file != historical_file:
        st.session_state.results_cache = {}  # Очищаем кэш
        st.session_state.historical_file = historical_file  # Сохраняем ссылку на текущий файл

city = None
city_data = None

# Интерфейс для выбора города
if historical_file is not None:
    data = load_data(historical_file)

    if all(col in data.columns for col in ["city", "timestamp", "temperature", "season"]):
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        cities = data["city"].unique()

        # Добавляем выбор типа анализа
        analysis_type = st.sidebar.radio(
            trans["analysis_type"],
            [trans["standard_analysis"], trans["parallel_analysis"]]
        )

        if st.sidebar.button(trans["run_analysis"]):
            with st.spinner(trans["analyzing"]):
                if analysis_type == trans["parallel_analysis"]:
                    results_dict, computation_time = analyze_all_cities(data, parallel=True)
                else:
                    results_dict, computation_time = analyze_all_cities(data, parallel=False)

                st.session_state.results_cache = results_dict  # Сохраняем все результаты в кэше

                if computation_time:
                    st.success(trans["analysis_completed"].format(computation_time=computation_time))

        # Выбор города
        city = st.sidebar.selectbox(trans["select_city"], cities)

        city_data = data[data["city"] == city]

        # Проверка наличия результатов для выбранного города в кэше
        if city in st.session_state.results_cache:
            result = st.session_state.results_cache[city]

            # Разбираем и отображаем результаты анализа
            descriptive_stats, temperature_plot, seasonal_plot, trend_plot, anomalies, slope, r_value, p_value, seasonal_stats = result

            # Вывод результатов
            st.subheader(f"{trans['descriptive_statistics']} {city}")
            st.write(descriptive_stats)

            st.subheader(trans["temperature_time_series"])
            st.pyplot(temperature_plot)

            st.subheader(trans["seasonal_statistics"])
            st.write(seasonal_stats)

            st.subheader(trans["seasonal_profiles"])
            st.pyplot(seasonal_plot)

            st.subheader(trans["long_term_trend"])
            st.pyplot(trend_plot)

            # Вывод информации о трендах
            st.subheader(trans["trend_analysis"])
            st.write(f"{trans['temperature_change']}: {slope:.3f}°C/год")
            st.write(f"{trans['r_squared']}: {r_value ** 2:.3f}")
            st.write(f"{trans['p_value']}: {p_value:.3e}")

            # Вывод информации об аномалиях
            st.subheader(trans["anomalies"])
            st.write(f"{trans['detected_anomalies']}: {len(anomalies)}")
            st.write(anomalies)
        else:
            # Если для выбранного города нет данных в кэше
            st.warning(trans["no_results_in_cache"])

# Форма для ввода API-ключа
api_key = st.sidebar.text_input(trans["enter_api_key"], type="password")


@st.cache_data
def get_weather_data(city, api_key):
    return get_current_weather(city, api_key)


with weather_container:
    # Кнопка для получения текущей погоды
    if st.sidebar.button(trans["current_weather"]):
        if api_key and city:
            st.subheader(trans["current_weather"])

            # Получаем данные о погоде (используем кэшированную функцию)
            weather_data = get_weather_data(city, api_key)

            if isinstance(weather_data, dict) and "error" in weather_data:
                st.error(trans["api_error"].format(message=weather_data["error"]))
            else:
                # Получаем текущую температуру
                current_temp = weather_data.temperature('celsius')["temp"]
                st.write(trans["current_temp"].format(city=city, current_temp=current_temp))

                # Проверяем температуру
                if city_data is not None and not city_data.empty:
                    analysis = check_current_temperature(current_temp, city_data)

                    if 'error' in analysis:
                        st.error(analysis['error'])
                    else:
                        if analysis['is_anomaly']:
                            st.warning(
                                trans["temperature_anomaly_warning"].format(
                                    season=analysis['season'],
                                    difference=analysis['difference'],
                                    mean_temp=analysis['mean_temp']
                                )
                            )
                        else:
                            st.success(
                                trans["temperature_normal"].format(
                                    season=analysis['season'],
                                    mean_temp=analysis['mean_temp']
                                )
                            )
        else:
            st.error(trans["error_key_city"])
