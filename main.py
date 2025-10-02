import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
from datetime import datetime

# Configuration depuis variables d'environnement
URL = "https://trouverunlogement.lescrous.fr/tools/41/search?bounds=4.7396309_43.9967419_4.9271468_43.8866492"
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 300))  # 5 minutes par défaut

# Configuration email depuis variables d'environnement
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER')

def check_logements():
    """Vérifie s'il y a des logements disponibles"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher les indicateurs de logements
        no_results = soup.find(string=lambda text: text and "Aucun logement trouvé" in text)
        
        if no_results:
            return False, 0, []
        
        # Si pas de message "aucun logement", il y a probablement des résultats
        logements = soup.find_all('div', class_='fr-card')
        
        logements_info = []
        for logement in logements:
            try:
                titre = logement.find('h3')
                prix = logement.find(string=lambda text: text and '€' in text)
                logements_info.append({
                    'titre': titre.text.strip() if titre else 'N/A',
                    'prix': prix.strip() if prix else 'N/A'
                })
            except:
                pass
        
        return len(logements_info) > 0, len(logements_info), logements_info
        
    except Exception as e:
        print(f"Erreur lors de la vérification: {e}")
        return False, 0, []

def send_email(nb_logements, logements_info):
    """Envoie un email de notification"""
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🏠 {nb_logements} nouveau(x) logement(s) CROUS disponible(s) à Avignon!"
        message["From"] = EMAIL_SENDER
        message["To"] = EMAIL_RECEIVER
        
        text_content = f"""
Bonjour,

{nb_logements} nouveau(x) logement(s) sont disponibles sur le site du CROUS à Avignon!

Consultez vite le site: {URL}

Détails des logements:
"""
        
        for i, logement in enumerate(logements_info, 1):
            text_content += f"\n{i}. {logement['titre']} - {logement['prix']}"
        
        text_content += f"\n\nDate de la notification: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        
        html_content = f"""
<html>
  <body>
    <h2>🏠 Nouveaux logements CROUS disponibles!</h2>
    <p><strong>{nb_logements}</strong> nouveau(x) logement(s) sont disponibles à Avignon.</p>
    <p><a href="{URL}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Voir les offres</a></p>
    <h3>Détails:</h3>
    <ul>
"""
        for logement in logements_info:
            html_content += f"<li><strong>{logement['titre']}</strong> - {logement['prix']}</li>"
        
        html_content += f"""
    </ul>
    <p style="color: #666; font-size: 12px;">Notification envoyée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
  </body>
</html>
"""
        
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, message.as_string())
        
        print(f"✅ Email envoyé avec succès! {nb_logements} logement(s) trouvé(s)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")
        return False

def main():
    """Fonction principale de surveillance"""
    print("🔍 Démarrage de la surveillance des logements CROUS Avignon...")
    print(f"📧 Notifications envoyées à: {EMAIL_RECEIVER}")
    print(f"⏱️  Vérification toutes les {CHECK_INTERVAL} secondes ({CHECK_INTERVAL//60} minutes)")
    print("-" * 60)
    
    # Vérification de la configuration
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        print("❌ ERREUR: Variables d'environnement EMAIL_SENDER, EMAIL_PASSWORD et EMAIL_RECEIVER requises!")
        return
    
    derniere_notification = None
    compteur_verifications = 0
    
    while True:
        try:
            compteur_verifications += 1
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
            print(f"\n[{timestamp}] Vérification #{compteur_verifications}...")
            
            disponible, nb_logements, logements_info = check_logements()
            
            if disponible and nb_logements > 0:
                print(f"✨ {nb_logements} logement(s) trouvé(s)!")
                
                if derniere_notification != nb_logements:
                    if send_email(nb_logements, logements_info):
                        derniere_notification = nb_logements
            else:
                print("Aucun logement disponible pour le moment.")
            
            print(f"⏳ Prochaine vérification dans {CHECK_INTERVAL//60} minutes...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Arrêt du script par l'utilisateur.")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            print(f"⏳ Nouvelle tentative dans {CHECK_INTERVAL//60} minutes...")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()