import streamlit as st  
import pandas as pd  

from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.common.exceptions import TimeoutException  

import os  
import glob  

def scrape_data_selenium(url):  
    """Scrapes data from a URL using Selenium."""  
    try:  
        # Configure Chrome options for headless browsing  
        chrome_options = Options()  
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode  
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model  
        chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems  
        
        # Initialize the Chrome driver  
        driver = webdriver.Chrome(options=chrome_options)  

        driver.get(url)  

        # Wait for the elements to load (adjust timeout as needed)  
        wait = WebDriverWait(driver, 10)  
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'listings-cards__list-item')))  

        # Find all listing containers  
        containers = driver.find_elements(By.CLASS_NAME, 'listings-cards__list-item')  
        data = []  

        for container in containers:  
            try:  
                # Extract data using Selenium  
                detail_elem = container.find_element(By.CLASS_NAME, 'listing-card__header__title')  
                prix_elem = container.find_element(By.CLASS_NAME, 'listing-card__price__value')  
                adresse_elem = container.find_element(By.CLASS_NAME, 'listing-card__header__location')  
                image_elem = container.find_element(By.CLASS_NAME, 'listing-card__image__inner').find_element(By.TAG_NAME, 'img')  

                condition_classes = [  
                    'listing-card__header__tags__item--condition_used',  
                    'listing-card__header__tags__item--condition_new',  
                    'listing-card__header__tags__item--condition_refurbished',  
                    'listing-card__header__tags__item--condition_used-abroad'  
                ]  

                etat = "Pas Disponible"  
                for cls in condition_classes:  
                    try:  
                        etat_elem = container.find_element(By.CLASS_NAME, cls)  
                        etat = etat_elem.text.strip()  
                        break  
                    except:  
                        pass  

                detail = detail_elem.text.strip() if detail_elem else "Pas Disponible"  
                prix_text = prix_elem.text.strip().replace('\u202f', '').replace(' F Cfa', '').replace(' ', '') if prix_elem else '0.0'  
                prix = float(prix_text) if prix_text else 0.0  
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

        driver.quit()  # Close the browser  
        return pd.DataFrame(data)  

    except Exception as e:  
        st.error(f"An error occurred: {e}")  
        return pd.DataFrame()  

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
    st.header("Scraping Results (Selenium)")  
    selected_url = f"{categories[url_selection]}?page={page_selection}"  
    with st.spinner('Scraping data with Selenium...'):  
        scraped_data = scrape_data_selenium(selected_url)  

    if not scraped_data.empty:  
        st.write(scraped_data)  
        st.success(f"Total des données scrapées: {len(scraped_data)}")  

    else:  
        st.warning("Aucune donnée Trouvée ou Scrapée.")  

elif option_selection == "Download Data":  
    st.header("Download Data")  

    if os.path.exists(csv_folder_path):  
        files = [f for f in os.listdir(csv_folder_path) if f.endswith('.csv')]  
        
        if files:  
            for file_name in files:  
                file_path = os.path.join(csv_folder_path, file_name)  
                with open(file_path, "rb") as file:  
                    st.download_button(f"Download {file_name}", file, file_name=file_name, mime="text/csv")  
        else:  
            st.warning("No CSV files available for download.")  
    else:  
        st.warning("The specified folder does not exist.")  

elif option_selection == "Dashboard":  
    st.header("Data Dashboard")  

    if os.path.exists(clean_dashboard_path):  
        files = glob.glob(os.path.join(clean_dashboard_path, "*.xlsx"))  
       
        if files:  
            for file_path in files:  
                st.subheader(f"Dashboard for {os.path.basename(file_path)}")  

                data = pd.read_excel(file_path)  
                st.write(data)  

                if 'Condition' in data.columns:  # Corrected column name  
                    st.subheader("Quantité des différents Elements de la colonne (Condition)")  
                    etat_counts = data['Condition'].value_counts()  # Corrected line  
                    st.bar_chart(etat_counts)  

                if 'Price (F Cfa)' in data.columns:  
                    st.subheader("Price Distribution")  
                    st.bar_chart(data['Price (F Cfa)'])  

        else:  
            st.warning("No Excel files available for dashboard analysis.")  
    else:  
        st.warning("The specified folder does not exist.")  

elif option_selection == "App Evaluation":  
    st.header("App Evaluation Form")  
    st.write("Please fill out the form below to provide feedback on the app:")  
    st.components.v1.iframe("https://ee.kobotoolbox.org/i/CHR2ME9Y", width=800, height=600)
