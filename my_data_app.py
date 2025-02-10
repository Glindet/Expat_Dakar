import streamlit as st
import pandas as pd
import os
import glob
from streamlit_option_menu import option_menu
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
from bs4 import BeautifulSoup as bs

# Function to get the Chrome WebDriver with headless configuration
def get_driver():
    options = Options()
    options.add_argument('--headless')  # Run Chrome in headless mode
    options.add_argument('--no-sandbox')  # Fix for some environments
    options.add_argument('--disable-dev-shm-usage')  # Workaround for limited resources
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Scraping function using Selenium
def scrape_data(url):  
    try:
        driver = get_driver()  # Get the headless driver
        driver.get(url)
        
        soup = bs(driver.page_source, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item')  
        data = []

        for container in containers:
            try:
                detail_elem = container.find('div', class_='listing-card__header__title')
                prix_elem = container.find('span', class_='listing-card__price__value')
                adresse_elem = container.find('div', class_='listing-card__header__location')
                image_elem = container.find('div', class_='listing-card__image__inner')

                condition_classes = [
                    'listing-card__header__tags__item--condition_used',
                    'listing-card__header__tags__item--condition_new',
                    'listing-card__header__tags__item--condition_refurbished',
                    'listing-card__header__tags__item--condition_used-abroad'
                ]

                etat = "Pas Disponible"
                for cls in condition_classes:
                    etat_elem = container.find('span', class_=cls)
                    if etat_elem:
                        etat = etat_elem.text.strip()
                        break

                detail = detail_elem.text.strip() if detail_elem else "Pas Disponible"
                prix = float(prix_elem.text.strip().replace('\u202f', '').replace(' F Cfa', '').replace(' ', '')) if prix_elem and prix_elem.text.strip() else 0.0
                adresse = adresse_elem.text.strip().replace(',\n', ' -').strip() if adresse_elem else "Pas Disponible"
                image_lien = image_elem.img['src'] if image_elem and image_elem.img else "Pas Disponible"

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

        driver.quit()  # Close the browser after scraping
        return pd.DataFrame(data)  

    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
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
    st.header("Scraping Results")  
    selected_url = f"{categories[url_selection]}?page={page_selection}"  
    with st.spinner('Scraping data...'):  
        scraped_data = scrape_data(selected_url)  

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

                if 'Etat' in data.columns:  
                    st.subheader("Quantité des différents Elements de la colonne (Etat)")  
                    etat_counts = data['Etat'].value_counts()  
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
