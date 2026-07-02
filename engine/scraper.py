from playwright.sync_api import sync_playwright


class GoogleMapsScraper:
    def run(self, query, depth):
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")

            # Scroll para carregar resultados
            for _ in range(depth):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(1000)

            items = page.query_selector_all('div[role="feed"] > div')
            for item in items:
                try:
                    name = item.query_selector('div.qBF1Pd').inner_text()
                    site_el = item.query_selector('a[data-value="Website"]')
                    site = site_el.get_attribute('href') if site_el else None
                    phone_el = item.query_selector('button[data-tooltip="Copy phone number"]')
                    phone = phone_el.get_attribute('aria-label') if phone_el else "N/A"

                    results.append({"Nome": name, "Telefone": phone, "Site": site, "Email": None})
                except:
                    continue
            browser.close()
        return results