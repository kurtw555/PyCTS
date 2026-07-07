from urllib.parse import quote

from .models import ForecastData, ForecastPeriod, PointMetadata
from .transport import HttpTransport


class NWSClient:
    BASE_URL = "https://api.weather.gov"

    def __init__(self, transport: HttpTransport):
        self.transport = transport

    def get_point_metadata(self, latitude: float, longitude: float) -> PointMetadata:
        url = f"{self.BASE_URL}/points/{latitude:.4f},{longitude:.4f}"
        payload = self.transport.get_json(url)
        props = payload.get("properties", {})
        relative = props.get("relativeLocation", {}).get("properties", {})
        point = props.get("gridId", "")

        return PointMetadata(
            latitude=latitude,
            longitude=longitude,
            grid_id=point,
            grid_x=int(props.get("gridX", 0)),
            grid_y=int(props.get("gridY", 0)),
            forecast_url=props.get("forecast", ""),
            forecast_hourly_url=props.get("forecastHourly", ""),
            forecast_grid_data_url=props.get("forecastGridData", ""),
            timezone=props.get("timeZone", relative.get("timeZone", "UTC")),
        )

    def get_forecast(self, url: str, units: str = "us") -> ForecastData:
        payload = self.transport.get_json(url, params={"units": units})
        props = payload.get("properties", {})
        periods = [ForecastPeriod.from_api(p) for p in props.get("periods", [])]
        return ForecastData(updated=props.get("updated", ""), units=units, periods=periods)


class GeocodingClient:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, transport: HttpTransport):
        self.transport = transport

    def geocode(self, query: str) -> tuple[float, float]:
        encoded = quote(query.strip())
        url = f"{self.NOMINATIM_URL}?q={encoded}&format=json&limit=1"
        payload = self.transport.get_json(url, headers={"Accept": "application/json"})
        if not isinstance(payload, list) or not payload:
            raise ValueError("Location not found")

        first = payload[0]
        return float(first.get("lat")), float(first.get("lon"))
