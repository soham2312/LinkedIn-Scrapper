from quart import Quart, request, jsonify, make_response
import asyncio
from pyppeteer import launch
from pyppeteer_stealth import stealth
from bs4 import BeautifulSoup

app = Quart(__name__)

# CORS Middleware
@app.after_request
async def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

async def fetch_linkedin_search_page(page, company_name):
    try:
        search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
        await page.goto(search_url, {'waitUntil': 'networkidle2'})
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        company_ids = set()
        for span_tag in soup.find_all('span', class_='entity-result__title-text t-16'):
            a_tag = span_tag.find('a', class_='app-aware-link', href=True)
            if a_tag:
                company_url = a_tag['href']
                company_id = company_url.split('/company/')[1].split('/')[0]
                company_ids.add(company_id)
        return list(company_ids)
    except Exception as e:
        print(f"An error occurred while fetching company IDs: {e}")
        return None

async def scroll_down(page):
    await page.evaluate('''() => {
        window.scrollBy(0, window.innerHeight);
    }''')
    await asyncio.sleep(1)

async def fetch_company_info(page, company_id, provided_website):
    try:
        company_url = f"https://www.linkedin.com/company/{company_id}/about/"
        await page.goto(company_url, {'waitUntil': 'networkidle2'})
        await scroll_down(page)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        company_name = soup.find('h1').text.strip()
        website_tag = soup.find('dd', {'class': 'mb4 t-black--light text-body-medium'})
        company_website = "N/A"
        if website_tag:
            link_tag = website_tag.find('a', {'href': True})
            company_website = link_tag['href'].strip() if link_tag else "N/A"
        normalized_provided_website = provided_website.replace("http://", "").replace("https://", "").rstrip('/')
        normalized_company_website = company_website.replace("http://", "").replace("https://", "").rstrip('/')
        industry = soup.find('dd', {'class': 'mb4 t-black--light text-body-medium'}).text.strip()
        company_size = None
        for dt_tag in soup.find_all('dt', {'class': 'mb1'}):
            if "Company size" in dt_tag.text:
                company_size = dt_tag.find_next('dd').text.strip()
                break
        headquarters = None
        for dt_tag in soup.find_all('dt', {'class': 'mb1'}):
            if "Headquarters" in dt_tag.text:
                headquarters = dt_tag.find_next('dd').text.strip()
                break
        founded = None
        for dt_tag in soup.find_all('dt', {'class': 'mb1'}):
            if "Founded" in dt_tag.text:
                founded = dt_tag.find_next('dd').text.strip()
                break
        specialties = None
        for dt_tag in soup.find_all('dt', {'class': 'mb1'}):
            if "Specialties" in dt_tag.text:
                specialties = dt_tag.find_next('dd').text.strip()
                break
        overview = soup.find('p', {'class': 'break-words white-space-pre-wrap t-black--light text-body-medium'})
        overview_text = overview.text.strip() if overview else "N/A"
        if normalized_provided_website in normalized_company_website:
            company_info = {
                'name': company_name,
                'website': company_website,
                'industry': industry,
                'company_size': company_size,
                'headquarters': headquarters,
                'founded': founded,
                'specialties': specialties,
                'overview': overview_text
            }
            return company_info
        else:
            return None
    except Exception as e:
        print(f"An error occurred while fetching company info: {e}")
        return None

async def scrape_linkedin(company_name, provided_website, email, password):
    try:
        browser = await launch(headless=True)
        page = await browser.newPage()
        await stealth(page)
        await page.goto('https://www.linkedin.com/login', {'waitUntil': 'networkidle2'})
        await page.waitForSelector('input[name="session_key"]')
        await page.waitForSelector('input[name="session_password"]')
        await page.waitForSelector('button[type="submit"]')
        await page.type('input[name="session_key"]', email, {'delay': 100})
        await page.type('input[name="session_password"]', password, {'delay': 100})
        await page.click('button[type="submit"]')
        try:
            await page.waitForNavigation({'waitUntil': 'networkidle2', 'timeout': 30000})
        except Exception as e:
            print(f"Navigation error: {e}")
        current_url = page.url
        if 'feed' in current_url or 'search' in current_url:
            print("Login successful")
        else:
            print("Login failed")
            await page.screenshot({'path': 'login_failed.png'})
            await browser.close()
            return
        company_ids = await fetch_linkedin_search_page(page, company_name)
        if company_ids:
            for company_id in company_ids:
                info = await fetch_company_info(page, company_id, provided_website)
                if info:
                    await browser.close()
                    return info
            await browser.close()
            return {"message": "No matching company website found."}
        else:
            await browser.close()
            return {"message": "No company IDs found."}
    except Exception as e:
        print(f"An error occurred in the scraping function: {e}")
        return {"error": str(e)}

@app.route('/scrape', methods=['POST'])
async def scrape():
    data = await request.json
    company_name = data.get('company_name')
    provided_website = data.get('provided_website')
    email = data.get('email')
    password = data.get('password')

    result = await scrape_linkedin(company_name, provided_website, email, password)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
