from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import sqlite3
import os
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()

profile = os.getenv('PROFILE')
password = os.getenv('PASSWORD')

print(profile)

# Funciones para la base de datos
def create_table():
    cur.execute('''CREATE TABLE insta (
                profile TEXT,
                user TEXT,
                name TEXT,
                img TEXT,
                follower INTEGER,
                following INTEGER,
                PRIMARY KEY (profile, user))''')

def insert_table(profile, user, name, img, mode):
    cur.execute('SELECT * FROM insta WHERE profile = ? AND user = ?', (profile, user))
    result = cur.fetchone()

    if mode==0:
        mode = "follower"
        follower = 1
        following = 0

    elif mode==1:
        mode = "following"
        following = 1
        follower = 0

    if result:
    # Si el registro existe, actualizar campos
        cur.execute(f'''
            UPDATE insta
            SET {mode} = ?
            WHERE profile = ? AND user = ?''', (1, profile, user))
        
    else:
        # Si el registro no existe, insertar un nuevo registro
        cur.execute('''
            INSERT INTO insta (profile, user, name, img, follower, following)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (profile, user, name, img, follower, following))
    con.commit()

con = sqlite3.connect('insta.db')
cur = con.cursor()

# Creamos la tabla
# create_table()


# Configuración del perfil de usuario de Chrome
chrome_options = webdriver.ChromeOptions() 
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--user-data-dir=C:/Users/pepol/AppData/Local/Google/Chrome/User Data')
chrome_options.add_argument('--profile-directory=Default') 

# Instalar el chromedriver automáticamente y configurar el servicio
service = Service(ChromeDriverManager().install())

# Inicializa el navegador
driver = webdriver.Chrome(service=service, options=chrome_options)

try:

    def extract(mode):

        if mode==0:
            follower_button = driver.find_element(By.CSS_SELECTOR, 'a[href*="follower"]')
            count = int("".join(filter(str.isdigit, follower_button.text)))
            follower_button.click()
            time.sleep(2)
        
        elif mode==1:
            following_button = driver.find_element(By.CSS_SELECTOR, 'a[href*="following"]')
            count = int("".join(filter(str.isdigit, following_button.text)))
            following_button.click()
            time.sleep(2)

        # Ventana emergente con segudidos/Seguidores
        dialog = driver.find_element(By.CSS_SELECTOR, 'div[role="dialog"]')
        # Lista de seguidores dentro de la ventana
        target_div = dialog.find_element(By.CSS_SELECTOR, 'div[style="height: auto; overflow: hidden auto;"]')
        # Padre de la lista, que incluye el scroll
        parent_div = target_div.find_element(By.XPATH, '..')

        last_height = driver.execute_script("return arguments[0].scrollHeight", parent_div)
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", parent_div)
            time.sleep(2)
            new_height = driver.execute_script("return arguments[0].scrollHeight", parent_div)

            if new_height == last_height:
                break
            last_height = new_height

        # Usuarios de la lista completa
        users_divs = target_div.find_elements(By.XPATH, './*/child::*')

        if len(users_divs) < count:
            close_button = dialog.find_element(By.CSS_SELECTOR, 'button[type="button"]')
            close_button.click()

            extract(mode)
        
        else:  

            for user_div in users_divs:
                # user = user_div.find_element(By.CSS_SELECTOR, 'a.notranslate[href*="/"][href*="/"]')
                photo = user_div.find_element(By.CSS_SELECTOR, 'img[src][crossorigin="anonymous"][alt*="Foto del perfil"]').get_attribute('src')
                user, name = user_div.find_elements(By.CSS_SELECTOR, 'span[dir="auto"]')

                insert_table(profile, user.text, name.text, photo, mode)
        
        close_button = dialog.find_element(By.CSS_SELECTOR, 'button[type="button"]')
        close_button.click()

    driver.get(f"https://www.instagram.com/{profile}/")
    time.sleep(2)
    
    # Llamamos a la función de Scrap para mode=0 (seguidores) y para el mode=1 (seguidos)
    extract(1)
    extract(0)

finally:
    driver.quit()