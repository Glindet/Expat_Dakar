import streamlit as st  
import pandas as pd  
from streamlit_option_menu import option_menu  
from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from webdriver_manager.chrome import ChromeDriverManager  
import os  
import glob  
import time  

def scrape_data(url):  
    options = Options()  
    options.add_argument("--headless")  # Run in headless mode  
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")  

    # Setup Chrome WebDriver  
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=options)  
    
    try:  
        driver.get(url)  
        time.sleep(3)  # Let the page load  

        containers = driver.find_elements(By.CSS_SELECTOR, 'div.listings-cards__list-item')  
        data = []  

        for container in containers:  
            try:  
                detail_elem = container.find_element(By.CSS_SELECTOR, 'div.listing-card__header__title')  
                prix_elem = container.find_element(By.CSS_SELECTOR, 'span.listing-card__price__value')  
                adresse_elem = container.find_element(By.CSS_SELECTOR, 'div.listing-card__header__location')  
                image_elem = container.find_element(By.CSS_SELECTOR, 'div.listing-card__image__inner img')  

                condition_classes = [  
                    'listing-card__header__tags__item--condition_used',  
                    'listing-card__header__tags__item--condition_new',  
                    'listing-card__header__tags__item--condition_refurbished',  
                    'listing-card__header__tags__item--condition_used-abroad'  
                ]  

                etat = "Pas Disponible"  
                for cls in condition_classes:  
                    try:  
                        etat_elem = container.find_element(By.CSS_SELECTOR, f'span.{cls}')  
                        if etat_elem:  
                            etat = etat_elem.text.strip()  
                            break  
                    except:  
                        continue  
                
                detail = detail_elem.text.strip() if detail_elem else "Pas Disponible"  
                prix = float(prix_elem.text.strip().replace('\u202f', '').replace(' F Cfa', '').replace(' ', '')) if prix_elem else 0.0  
                adresse = adresse_elem.text.strip().replace(',\n', ' -').strip() if adresse_elem else "Pas Disponible"  
                image_lien = image_elem.get_attribute('src') if image_elem else "Pas Disponible"  

                dic = {  
                    'Details': detail,  
                    'Condition': etat,  
                    'Price (F Cfa)': prix,  
                    'Address': adresse,  
                    'Image Link': image_lien  
                }  
                data.append(dic)  

            except Exception as inner_e:  
                st.error(f"Error processing item: {inner_e}")  

        return pd.DataFrame(data)  
    
    except Exception as e:  
        st.error(f"Extraction failed: {e}")  
        return pd.DataFrame()  
    
    finally:  
        driver.quit()  # Close the browser  

# Sidebar configuration  
st.sidebar.title("Expat Dakar")  

categories = {  
    "Refrigerateurs Congélateurs": "https://www.expat-dakar.com/refrigerateurs-congelateurs",  
    "Climatisation": "https://www.expat-dakar.com/climatisation",  
    "Cuisinières et Fours": "https://www.expat-dakar.com/cuisinieres-fours",  
    "Machines à Laver": "https://www.expat-dakar.com/machines-a-laver",  
}  

url_selection = st.sidebar.selectbox("Choisissez une Catégorie:", list(categories.keys()))  

if url_selection:  
    pages = range(1, 18)  
    page_selection = st.sidebar.selectbox("Choisissez le numero de la page :", pages)  

options = ["Select...", "Scrape Data with Selenium", "Download Data", "Dashboard", "App Evaluation"]  
option_selection = st.sidebar.selectbox("Option:", options)  

csv_folder_path = r'data'  
clean_dashboard_path = r'clean_dashboard'  

# Processing selections  
if option_selection == "Scrape Data with Selenium":  
    st.header("Scraping Results")  
    selected_url = f"{categories[url_selection]}?page={page_selection}"  
    with st.spinner('Scraping data...'):  
        scraped_data = scrape_data(selected_url)  

    if not scraped_data.empty:  
        st.write(scraped_data)  
        st.success(f"Total des données scrapées: {len(scraped_data)}")  
    else:  
        st.warning("Aucune donnée Trouvée ou Scrapée.")  

# ... Rest of your handling code remains same ...  
# Download Data, Dashboard, App Evaluation sections should remain unchanged.
