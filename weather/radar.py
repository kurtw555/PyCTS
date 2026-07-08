from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

from .transport import HttpTransport


@dataclass
class RadarFrame:
    valid_time_ms: int
    label_utc: str


class RadarTimeIndexService:
    IMAGE_SERVER_URL = (
        "https://mapservices.weather.noaa.gov/eventdriven/rest/services/"
        "radar/radar_base_reflectivity_time/ImageServer"
    )

    def __init__(self, user_agent: str):
        self.transport = HttpTransport(user_agent=user_agent)

    def get_recent_frames(self, limit: int = 60) -> list[RadarFrame]:
        url = f"{self.IMAGE_SERVER_URL}/query"
        payload = self.transport.get_json(
            url,
            params={
                "where": "1=1",
                "returnGeometry": "false",
                "outFields": "idp_validtime",
                "returnDistinctValues": "true",
                "orderByFields": "idp_validtime DESC",
                "resultRecordCount": str(limit),
                "f": "pjson",
            },
            headers={"Accept": "application/json"},
        )

        features = payload.get("features", [])
        unique_times = set()
        for feature in features:
            attrs = feature.get("attributes", {})
            valid_time = attrs.get("idp_validtime") or attrs.get("IDP_ValidTime")
            if valid_time is None:
                continue
            try:
                unique_times.add(int(valid_time))
            except (TypeError, ValueError):
                continue

        sorted_times = sorted(unique_times, reverse=True)
        return [
            RadarFrame(valid_time_ms=ms, label_utc=self._format_utc_label(ms))
            for ms in sorted_times
        ]

    @classmethod
    def build_export_image_url(
        cls,
        bbox_3857: tuple[float, float, float, float],
        width_px: int,
        height_px: int,
        time_ms: int | None,
    ) -> str:
        params = {
            "f": "image",
            "bbox": ",".join(str(v) for v in bbox_3857),
            "bboxSR": "3857",
            "imageSR": "3857",
            "size": f"{width_px},{height_px}",
            "format": "png32",
            "transparent": "true",
        }
        if time_ms is not None:
            params["time"] = str(time_ms)
        return f"{cls.IMAGE_SERVER_URL}/exportImage?{urlencode(params)}"

    def _format_utc_label(self, valid_time_ms: int) -> str:
        dt = datetime.fromtimestamp(valid_time_ms / 1000, tz=UTC)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
