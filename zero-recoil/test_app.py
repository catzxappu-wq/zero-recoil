"""
ZERO RECOIL - Automated Comprehensive Test Suite
ARMUGA X CATZX
"""
import unittest
import json
import io
from app import app
from database import get_db, init_db, seed_db

class ZeroRecoilTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_database_seeded(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM admins")
        admins = cursor.fetchone()[0]
        self.assertGreaterEqual(admins, 2)

        cursor.execute("SELECT COUNT(*) FROM guns")
        guns = cursor.fetchone()[0]
        self.assertGreaterEqual(guns, 28)

        cursor.execute("SELECT COUNT(*) FROM brands")
        brands = cursor.fetchone()[0]
        self.assertGreaterEqual(brands, 20)

        cursor.execute("SELECT COUNT(*) FROM sensitivities")
        sens = cursor.fetchone()[0]
        self.assertGreaterEqual(sens, 20)
        conn.close()

    def test_02_public_pages(self):
        pages = ["/", "/guns", "/guns/mp40", "/devices", "/sensitivity", "/updates", "/about", "/contact", "/login", "/register"]
        for p in pages:
            res = self.client.get(p)
            self.assertEqual(res.status_code, 200, f"Failed on page {p}")
            self.assertIn(b"ZERO", res.data)
            self.assertIn(b"ARMUGA", res.data)

    def test_03_api_endpoints(self):
        # 1. Brands API
        res = self.client.get("/api/brands")
        self.assertEqual(res.status_code, 200)
        brands = res.get_json()
        self.assertIsInstance(brands, list)
        self.assertGreater(len(brands), 10)

        # 2. Devices API
        res = self.client.get("/api/devices")
        self.assertEqual(res.status_code, 200)
        devices = res.get_json()
        self.assertIsInstance(devices, list)
        self.assertGreater(len(devices), 10)

        # 3. Device Details API
        dev_id = devices[0]["id"]
        res = self.client.get(f"/api/device/{dev_id}/details")
        self.assertEqual(res.status_code, 200)
        dev_details = res.get_json()
        self.assertIn("rams", dev_details)
        self.assertIn("processor", dev_details)

        # 4. Search API
        res = self.client.get("/api/search?q=poco")
        self.assertEqual(res.status_code, 200)
        search_res = res.get_json()
        self.assertIn("devices", search_res)

        # 5. Sensitivity lookup (The POCO M6 5G + MP40 prompt example!)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM guns WHERE slug = 'mp40'")
        gun_id = cursor.fetchone()[0]
        cursor.execute("SELECT id, processor FROM devices WHERE slug = 'poco-m6-5g'")
        dev_row = cursor.fetchone()
        dev_id = dev_row[0]
        proc = dev_row[1]
        conn.close()

        res = self.client.get(f"/api/sensitivity/lookup?gun_id={gun_id}&device_id={dev_id}&ram=6%20GB&processor={proc}")
        self.assertEqual(res.status_code, 200)
        sens_data = res.get_json()
        self.assertTrue(sens_data.get("found"))
        self.assertEqual(sens_data["sensitivity"]["general"], 98)
        self.assertEqual(sens_data["sensitivity"]["red_dot"], 96)

    def test_04_customer_flow(self):
        # Register new player
        res = self.client.post("/register", data={
            "name": "TestProPlayer",
            "email": "testplayer@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"TestProPlayer", res.data)

        # Access dashboard
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"PLAYER DASHBOARD", res.data)

        # Save sensitivity
        res = self.client.post("/api/save-sensitivity", json={"sensitivity_id": 1})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("success"))

        # Check saved sensitivities page
        res = self.client.get("/saved")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"SAVED SENSITIVITIES", res.data)

        # Logout
        res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_05_admin_flow(self):
        # 1. Login as ARMUGA
        res = self.client.post("/admin/login", data={
            "email": "armuga@zerorecoil.gg",
            "password": "armuga1234"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ZERO RECOIL ADMIN PANEL", res.data)
        self.assertIn(b"ARMUGA", res.data)

        # 2. Access admin guns
        res = self.client.get("/admin/guns")
        self.assertEqual(res.status_code, 200)

        # 3. Access admin devices
        res = self.client.get("/admin/devices")
        self.assertEqual(res.status_code, 200)

        # 4. Access admin sensitivities
        res = self.client.get("/admin/sensitivities")
        self.assertEqual(res.status_code, 200)

        # 5. Export CSV
        res = self.client.get("/admin/export-csv")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/csv")

        # 6. Sample CSV
        res = self.client.get("/admin/sample-csv")
        self.assertEqual(res.status_code, 200)

        # 7. Update Live Stream
        res = self.client.post("/admin/live/update", data={
            "is_live": "1",
            "title": "🔴 ARMUGA X CATZX IS LIVE - TESTING FF HEADSHOT SENSITIVITIES",
            "stream_url": "https://youtube.com/@armugaxcatzx/live"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 8. Check homepage shows live banner
        res = self.client.get("/")
        self.assertIn(b"ARMUGA X CATZX IS LIVE", res.data)

        # 9. Admin Logout
        res = self.client.get("/admin/logout", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 10. Login as CATZX
        res = self.client.post("/admin/login", data={
            "email": "catzx@zerorecoil.gg",
            "password": "catzx1234"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CATZX", res.data)

if __name__ == "__main__":
    unittest.main()
