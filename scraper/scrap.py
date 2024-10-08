from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time
from dotenv import load_dotenv
from .models import Insta, Profile

def start_scraping(input_user=None, input_password=None, admin=False):
    try_login = False
    # Comprobamos si se hace un scrap con admin o con credenciales manuales
    if admin and not input_password:
        if not input_user:
            # Cargamos credenciales propias
            load_dotenv()
            profile = os.getenv('PROFILE')
            password = os.getenv('PASSWORD')
        else:
            # Buscamos perfil público
            profile = input_user
    else:
        # Iniciamos sesión
        profile = input_user
        password = input_password
        try_login = True
    
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

    # Instalar el chromedriver automáticamente e iniciar el navegador
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        if try_login:

            # Iniciar sesión en Instagram
            driver.get("https://www.instagram.com/accounts/login/")

            # Esperar a que los campos de usuario y contraseña sean visibles
            username_input = wait.until(EC.visibility_of_element_located((By.NAME, 'username')))
            password_input = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))
            
            # Ingresar credenciales
            username_input.send_keys(profile)
            password_input.send_keys(password)

            # Clic en el botón de inicio de sesión
            login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            time.sleep(10)

    except:
        print("Datos incorrectos o doble verificación.")
        driver.quit()
        return "Datos incorrectos o doble verificación"
    
    else:

        try:
            driver.get(f"https://www.instagram.com/{profile}/")
            page_source = driver.page_source

            # Cuenta No Existe
            if "Esta página no está disponible." in page_source:
                print("Usuario no existe.")
                driver.quit()
                return "Usuario no existe"
            # Cuenta Privada
            elif "Esta cuenta es privada" in page_source:
                print("Usuario privado.")
                driver.quit()
                return "Usuario privado"
            #Público o credenciales
            else: 
                Insta.objects.filter(profile=profile).delete()
                extract(0, profile, driver)
                extract(1, profile, driver)
        except:
            print("Error durante scrap.")
            driver.quit()
            return "Error durante scrap"
        
        else:
            print("Scrap finalizado.")
            driver.quit()
            return "Scrap finalizado"

def extract(mode, profile, driver):
    wait = WebDriverWait(driver, 4)

    # Obtener datos del perfil
    try:
        photo = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[src][alt*="Cambiar foto del perfil"]'))).get_attribute('src')
    except:
        photo = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[src][alt*="Foto del perfil"]'))).get_attribute('src')

    print(photo)
    followers_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/followers/"]')))
    followings_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/following/"]')))
    followers = int("".join(filter(str.isdigit, followers_element.text)))
    followings = int("".join(filter(str.isdigit, followings_element.text)))

    # Obtener datos perfil
    insert_profile(profile, photo, followers, followings)

    if mode==0:
        count = int(followers)
        followers_element.click()

    elif mode==1:
        count = int(followings)
        followings_element.click()

    # Ventana emergente con segudidos/Seguidores
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]')))
    # Lista de perfiles dentro de la ventana
    target_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[style="height: auto; overflow: hidden auto;"]')))
    # Padre de la lista, que incluye el scroll
    parent_div = target_div.find_element(By.XPATH, '..')

    last_height = driver.execute_script("return arguments[0].scrollHeight", parent_div)
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", parent_div)
        try:
            wait.until(lambda d: driver.execute_script("return arguments[0].scrollHeight", parent_div) > last_height)
            new_height = driver.execute_script("return arguments[0].scrollHeight", parent_div)
            last_height = new_height

        except:
            break

    # Usuarios de la lista completa
    users_divs = target_div.find_elements(By.XPATH, './*/child::*')

    if len(users_divs) < count:
        close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="button"]')))
        close_button.click()

        extract(mode, profile, driver)

    else:  

        for user_div in users_divs:
            # user = user_div.find_element(By.CSS_SELECTOR, 'a.notranslate[href*="/"][href*="/"]')
            photo = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[src][crossorigin="anonymous"][alt*="Foto del perfil"]'))).get_attribute('src')
            user, name = wait.until(lambda driver: user_div.find_elements(By.CSS_SELECTOR, 'span[dir="auto"]'))

            insert_insta(profile, user.text, name.text, photo, mode)

    close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="button"]')))
    close_button.click()


def insert_insta(profile, user, name, img, mode):
    result = Insta.objects.filter(profile=profile, user=user).first()

    if mode==0:
        mode = "follower"
        follower = True
        following = False

    elif mode==1:
        mode = "following"
        following = True
        follower = False

    if result:
        # Si el registro existe, actualizar campos
        if mode == "follower":
            result.follower = True
        elif mode == "following":
            result.following = True
        result.save()  # Guardar los cambios
    
    else:
        # Si el registro no existe, insertar un nuevo registro
        Insta.objects.create(
            profile=profile,
            user=user,
            name=name,
            img=img,
            follower=follower,
            following=following)
        
def insert_profile(profile, photo, followers, followings):
    result = Profile.objects.filter(profile=profile)
    if result.exists():
        result = result.first()
        # Si el registro existe, actualizar datos
        result.img = photo
        result.followers = followers
        result.followings = followings
        result.save()
    
    else:
        # Si el registro no existe, insertar un nuevo registro
        Profile.objects.create(
            profile=profile,
            img=photo,
            followers=followers,
            followings=followings)