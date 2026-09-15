"""Ajoute de petits PDF de démonstration au catalogue.
Exécution : python seed_demo.py
"""
import os
from database import init_db
from models import create_book, get_books
from app import UPLOAD_DIR

try:
    from reportlab.pdfgen import canvas
except ImportError:
    raise SystemExit("Installez reportlab uniquement pour les démos : pip install reportlab")

init_db()
items = [
    ("Introduction à HTML", "DEKAL", "Apprends les bases du HTML.", "Développement web", "demo_html.pdf"),
    ("JavaScript pour débutants", "DEKAL", "Premiers concepts de JavaScript.", "Programmation", "demo_js.pdf"),
    ("Python pour débutants", "DEKAL", "Découvre les bases de Python.", "Programmation", "demo_python.pdf"),
    ("Introduction à la cybersécurité", "DEKAL", "Concepts essentiels de sécurité informatique.", "Cybersécurité", "demo_cyber.pdf"),
    ("Les bases du Business", "DEKAL", "Notions fondamentales pour débuter en business.", "Business", "demo_business.pdf"),
]
existing = {x["filename"] for x in get_books(per_page=100)["items"]}
for title, author, desc, cat, filename in items:
    if filename in existing:
        continue
    path = os.path.join(UPLOAD_DIR, filename)
    c = canvas.Canvas(path)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, 760, title)
    c.setFont("Helvetica", 11)
    c.drawString(60, 735, desc)
    c.drawString(60, 700, "Document de démonstration DEKAL Books.")
    c.save()
    create_book(title, author, desc, cat, filename, os.path.getsize(path))
print("Données de démonstration créées.")
