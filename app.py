from flask import Flask, jsonify, request
from flask_cors import CORS

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

import time
import re

# ==========================================
# FLASK APP
# ==========================================
app = Flask(__name__)

app.json.ensure_ascii = False

CORS(app)

# ==========================================
# HOME ROUTE
# ==========================================
@app.route('/')
def home():

    return jsonify({
        "status": True,
        "message": "Medicine API Running Successfully"
    })

# ==========================================
# MEDICINE API
# ==========================================
@app.route('/medicine', methods=['GET'])
def medicine():

    # ==========================================
    # GET ARRAY INPUT
    # EXAMPLE:
    # ?name=[dolo 650,crocin,pan-d]
    # ==========================================
    medicine_input = request.args.get("name")

    if not medicine_input:

        return jsonify({
            "status": False,
            "message": "Medicine names required"
        })

    # ==========================================
    # STRING TO ARRAY
    # ==========================================
    medicine_input = medicine_input.replace("[", "")
    medicine_input = medicine_input.replace("]", "")

    medicines = medicine_input.split(",")

    medicines = [m.strip() for m in medicines]

    # ==========================================
    # CHROME OPTIONS
    # ==========================================
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # ==========================================
    # FINAL RESULT
    # ==========================================
    final_result = []

    try:

        # ==========================================
        # LOOP ALL MEDICINES
        # ==========================================
        for medicine_name in medicines:

            print("\n================================")
            print("Searching:", medicine_name)
            print("================================\n")

            # ==========================================
            # SEARCH URL
            # ==========================================
            search_url = f"https://www.1mg.com/search/all?name={medicine_name}"

            driver.get(search_url)

            time.sleep(5)

            medicine_url = ""

            # ==========================================
            # FIND MEDICINE LINK
            # ==========================================
            links = driver.find_elements(By.TAG_NAME, "a")

            for link in links:

                href = link.get_attribute("href")

                if href and "/drugs/" in href:

                    medicine_url = href
                    break

            # ==========================================
            # MEDICINE NOT FOUND
            # ==========================================
            if medicine_url == "":

                final_result.append({

                    "status": False,

                    "searched_name": medicine_name,

                    "message": "Medicine not found",

                    "Medicine Name": "N/A",

                    "Manufacturer": "N/A",

                    "Salt Composition": "N/A",

                    "Storage": "N/A",

                    "Prescription Required": "N/A",

                    "Pack Type": "N/A",

                    "Quantity": "N/A",

                    "Medicine URL": "N/A"
                })

                continue

            print("Medicine URL:", medicine_url)

            # ==========================================
            # OPEN PAGE
            # ==========================================
            driver.get(medicine_url)

            time.sleep(5)

            soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )

            # ==========================================
            # MEDICINE TITLE
            # ==========================================
            medicine_title = "N/A"

            title = soup.find("h1")

            if title:

                medicine_title = title.text.strip()

            # ==========================================
            # PAGE TEXT
            # ==========================================
            all_text = soup.get_text("\n", strip=True)

            lines = all_text.split("\n")

            lines = [
                line.strip()
                for line in lines
                if line.strip()
            ]

            # ==========================================
            # DEFAULT VALUES
            # ==========================================
            manufacturer = "N/A"
            salt = "N/A"
            storage = "N/A"
            quantity = "N/A"

            prescription_required = "No"

            pack_type = "Unknown"

            # ==========================================
            # EXTRACT DATA
            # ==========================================
            for i, line in enumerate(lines):

                # MANUFACTURER
                if line.upper() == "MARKETER":

                    if i + 1 < len(lines):

                        manufacturer = lines[i + 1]

                # SALT
                if line.upper() == "SALT COMPOSITION":

                    if i + 1 < len(lines):

                        salt = lines[i + 1]

                # STORAGE
                if line.upper() == "STORAGE":

                    if i + 1 < len(lines):

                        storage = lines[i + 1]

            # ==========================================
            # PRESCRIPTION REQUIRED
            # ==========================================
            page_text = soup.get_text(
                " ",
                strip=True
            ).lower()

            if "prescription required" in page_text:

                prescription_required = "Yes"

            # ==========================================
            # PACK TYPE
            # ==========================================
            title_lower = medicine_title.lower()

            if "tablet" in title_lower:

                pack_type = "Tablet"

            elif "capsule" in title_lower:

                pack_type = "Capsule"

            elif "syrup" in title_lower:

                pack_type = "Syrup"

            elif "injection" in title_lower:

                pack_type = "Injection"

            elif "cream" in title_lower:

                pack_type = "Cream"

            elif "ointment" in title_lower:

                pack_type = "Ointment"

            elif "gel" in title_lower:

                pack_type = "Gel"

            # ==========================================
            # QUANTITY EXTRACTION
            # ==========================================
            try:

                page_text_full = soup.get_text(
                    " ",
                    strip=True
                )

                quantity_patterns = [

                    # TABLETS
                    r'(\d+\.?\d*\s*tablets?\s+in\s+1\s+strip)',

                    # CAPSULES
                    r'(\d+\.?\d*\s*capsules?\s+in\s+1\s+strip)',

                    # CAPSULE PR
                    r'(\d+\.?\d*\s*capsule\s*pr\s+in\s+1\s+strip)',

                    # TABLET PR
                    r'(\d+\.?\d*\s*tablet\s*pr\s+in\s+1\s+strip)',

                    # GENERAL STRIP
                    r'(\d+\.?\d*.*?in\s+1\s+strip)',

                    # ML BOTTLE
                    r'(\d+\.?\d*\s*ml\s+bottle)',

                    # PACK
                    r'(\d+\.?\d*\s*pack)',

                ]

                for pattern in quantity_patterns:

                    match = re.search(
                        pattern,
                        page_text_full,
                        re.IGNORECASE
                    )

                    if match:

                        quantity = match.group(1)

                        break

            except Exception as e:

                print("Quantity Error:", e)

            # ==========================================
            # CLEAN EMPTY VALUES
            # ==========================================
            if not manufacturer:
                manufacturer = "N/A"

            if not salt:
                salt = "N/A"

            if not storage:
                storage = "N/A"

            if not quantity:
                quantity = "N/A"

            # ==========================================
            # PRINT TERMINAL
            # ==========================================
            print("Medicine:", medicine_title)
            print("Manufacturer:", manufacturer)
            print("Salt:", salt)
            print("Storage:", storage)
            print("Prescription:", prescription_required)
            print("Pack Type:", pack_type)
            print("Quantity:", quantity)

            # ==========================================
            # FINAL JSON
            # ==========================================
            medicine_data = {

            

                "searched_name": medicine_name,

                "Medicine Name": medicine_title,

                "Manufacturer": manufacturer,

                "Salt Composition": salt,

                "Storage": storage,

                "Prescription Required": prescription_required,

                "Pack Type": pack_type,

                "Quantity": quantity,

                "Medicine URL": medicine_url
            }

            final_result.append(medicine_data)

        return jsonify(final_result)

    except Exception as e:

        return jsonify({

            "status": False,

            "message": str(e)
        })

    finally:

        driver.quit()

# ==========================================
# RUN APP
# ==========================================
if __name__ == '__main__':

    app.run(debug=True)