from pyowm import OWM


def get_current_weather(city, api_key):
    """Получение текущей погоды через pyowm"""
    owm = OWM(api_key)
    mgr = owm.weather_manager()

    try:
        observation = mgr.weather_at_place(city)
        return observation.weather
    except Exception as e:
        return {"error": str(e)}
