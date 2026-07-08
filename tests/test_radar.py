import unittest
from urllib.parse import parse_qs, urlparse

from weather.radar import RadarTimeIndexService


class FakeTransport:
    def __init__(self, payload):
        self.payload = payload

    def get_json(self, *_args, **_kwargs):
        return self.payload


class RadarServiceTests(unittest.TestCase):
    def test_recent_frames_are_deduped_and_sorted(self):
        payload = {
            "features": [
                {"attributes": {"idp_validtime": 1783521100000}},
                {"attributes": {"idp_validtime": 1783521100000}},
                {"attributes": {"idp_validtime": 1783520800000}},
                {"attributes": {"IDP_ValidTime": 1783521400000}},
            ]
        }

        service = RadarTimeIndexService("TestAgent/1.0")
        service.transport = FakeTransport(payload)

        frames = service.get_recent_frames(limit=10)

        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0].valid_time_ms, 1783521400000)
        self.assertEqual(frames[1].valid_time_ms, 1783521100000)
        self.assertEqual(frames[2].valid_time_ms, 1783520800000)
        self.assertIn("UTC", frames[0].label_utc)

    def test_export_image_url_contains_expected_parameters(self):
        url = RadarTimeIndexService.build_export_image_url(
            bbox_3857=(-100.0, 20.0, -90.0, 30.0),
            width_px=1200,
            height_px=800,
            time_ms=1783521100000,
        )

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        self.assertIn("/ImageServer/exportImage", parsed.path)
        self.assertEqual(query.get("f", [None])[0], "image")
        self.assertEqual(query.get("bboxSR", [None])[0], "3857")
        self.assertEqual(query.get("imageSR", [None])[0], "3857")
        self.assertEqual(query.get("size", [None])[0], "1200,800")
        self.assertEqual(query.get("transparent", [None])[0], "true")
        self.assertEqual(query.get("time", [None])[0], "1783521100000")


if __name__ == "__main__":
    unittest.main()
