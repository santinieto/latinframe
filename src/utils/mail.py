# Imports estándar de Python
import os
# import sys

# Añade el directorio raíz del proyecto a sys.path
# current_path = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_path, '..', '..'))  # Ajusta según la estructura de tu proyecto
# sys.path.append(project_root)

# Imports de terceros
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Imports locales
from src.logger.logger import Logger

################################################################################
# Genero una instancia del Logger
################################################################################
logger = Logger(os.path.basename(__file__)).get_logger()

def send_mail(subject='Subject', message='Body', dest='santi.nieto@live.com', filename=None, show_mail=True):

    # Crear un objeto MIMEMultipart
    mail = MIMEMultipart()

    mail['From'] = os.environ["EMAIL_ADRESS"]
    mail['To'] = dest
    mail['Subject'] = subject

    # Evito un error
    if message is None:
        message = ''
    mail['message'] = message

    # Adjuntar el archivo, si se proporciona
    attached_file = False
    if filename is not None:
        try:
            with open(filename, "rb") as adjunto:
                archivo_mime = MIMEApplication(adjunto.read(), _subtype="pdf")  # Cambia "pdf" según el tipo de archivo
                archivo_mime.add_header('Content-Disposition', 'attachment', filename=filename)
                mail.attach(archivo_mime)
                attached_file = True
        except Exception as e:
            logger.error(f'Could not find file [{filename}] for email. Error: {e}')

    # Agregar el contenido del correo
    mail.attach(MIMEText(message, 'plain'))

    # Iniciar la conexión con el servidor SMTP de Gmail (puedes cambiar esto para otros proveedores de correo)
    if os.environ["EMAIL_PLATFORM"] == 'outlook':
        server_smtp = smtplib.SMTP('smtp-mail.outlook.com', 587)
        server_smtp.starttls()

    # Mensaje de error
    else:
        logger.error(f'No se pudo encontrar una plataforma para enviar el correo.')
        return

    # Iniciar sesión en la cuenta de Gmail
    server_smtp.login(os.environ["EMAIL_ADRESS"], os.environ["EMAIL_PASSWORD"])

    # Enviar el correo electrónico
    texto_del_correo = mail.as_string()
    server_smtp.sendmail(os.environ["EMAIL_ADRESS"], dest, texto_del_correo)

    # Cerrar la conexión con el servidor SMTP
    server_smtp.quit()

    # Muestro el correo
    if show_mail is True:
        logger.info(f"""
            From: {mail['From']}
            To: {mail['To']}
            Subject: {mail['Subject']}
            Content: {mail['message']}
            """)

if __name__ == '__main__':

    # Seteo variables de entorno
    os.environ["EMAIL_ADRESS"] = 'santi.nieto@live.com'
    os.environ["EMAIL_PASSWORD"] = 'N32hq7.003s'
    os.environ["EMAIL_PLATFORM"] = 'outlook'

    # Envio un correo y adjunto un archivo
    send_mail(filename='test.pdf')