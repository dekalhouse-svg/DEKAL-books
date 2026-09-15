import getpass
from werkzeug.security import generate_password_hash

password = getpass.getpass("Mot de passe administrateur: ")
print("\nADMIN_PASSWORD_HASH=" + generate_password_hash(password))
