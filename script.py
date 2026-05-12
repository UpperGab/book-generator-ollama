#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
import uuid
import time
from datetime import datetime
import ollama
from ebooklib import epub
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ========== CONFIGURATION ==========
MODEL_NAME = "llama3.2:latest"          # Modèle Ollama
FONT_PATH = "fonts/cnr.otf"             # Police OTF (chemin relatif)
OUTPUT_DIR = "rendu"                    # Dossier de sortie
AUTHOR_NAME = "Astin Java"              # Nom d'auteur public
# ===================================

def ensure_output_dir():
    """Crée le dossier de sortie en chemin absolu."""
    abs_path = os.path.abspath(OUTPUT_DIR)
    os.makedirs(abs_path, exist_ok=True)
    print(f"📁 Dossier de sortie : {abs_path}")
    return abs_path

def ask_book_details():
    print("\n📖 Création d'un nouveau livre")
    print("-" * 40)
    subject = input("Sujet principal du livre : ").strip()
    if not subject:
        print("Sujet requis.")
        sys.exit(1)
    details = input("Détails supplémentaires (ambiance, personnages, style) : ").strip()
    chap_choice = input("Nombre de chapitres ? (Entrée pour aléatoire 3-8) : ").strip()
    if chap_choice.isdigit():
        num_chapters = int(chap_choice)
    else:
        num_chapters = random.randint(3, 8)
    print(f"\n✅ {num_chapters} chapitres sur '{subject}'")
    return subject, details, num_chapters

def generate_chapter(chapter_num, title, subject, details):
    prompt = f"""
Écris le chapitre {chapter_num} du livre sur "{subject}", titre : "{title}".
Consignes : {details}
Style romanesque, 800-1200 mots. Structure : ## Titre puis paragraphes.
Rends le contenu vivant et cohérent. Ne donne que le texte du chapitre.
"""
    print(f"  ✍️ Chapitre {chapter_num} : '{title}'...")
    try:
        resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        return resp['message']['content']
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return f"## {title}\n\n(Erreur de génération pour ce chapitre.)\n\n"

def generate_chapter_titles(subject, num_chapters):
    prompt = f"Donne exactement {num_chapters} titres de chapitres pour un livre sur '{subject}'. Un titre par ligne, rien d'autre."
    try:
        resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        raw = resp['message']['content']
        titles = []
        for line in raw.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Supprime les numéros en début de ligne (ex: "1. Titre" -> "Titre")
            if line[0].isdigit() and (len(line) > 1 and line[1] in '. -)'):
                line = line.split(' ', 1)[-1].strip()
            if line.lower().startswith(('voici', 'liste', 'génère')):
                continue
            titles.append(line)
        if len(titles) < num_chapters:
            titles += [f"Chapitre {i+1}" for i in range(len(titles), num_chapters)]
        return titles[:num_chapters]
    except Exception as e:
        print(f"⚠️ Erreur génération titres : {e}")
        return [f"Chapitre {i+1}" for i in range(num_chapters)]

def create_cover_image(book_title, output_path):
    """Génère une image de couverture, avec création forcée du dossier parent."""
    # Convertir en chemin absolu
    abs_path = os.path.abspath(output_path)
    parent = os.path.dirname(abs_path)
    os.makedirs(parent, exist_ok=True)
    print(f"📁 Sauvegarde couverture dans : {parent}")
    
    # Vérifier les droits en écriture (optionnel mais prudent)
    if not os.access(parent, os.W_OK):
        print(f"⚠️ Pas de droit d'écriture dans {parent}, utilisation du répertoire courant.")
        abs_path = os.path.abspath("cover_temp.jpg")
    
    # Dimensions et fond
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='#1a2a3a')
    draw = ImageDraw.Draw(img)
    
    # Police (fallback si la police système n'existe pas)
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        author_font = ImageFont.truetype("arial.ttf", 40)
    except:
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    # Petits cercles décoratifs
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(1, 5)
        draw.ellipse([x-r, y-r, x+r, y+r], fill='#ffd966')
    
    # Titre avec retour à la ligne
    wrapped = textwrap.wrap(book_title, width=25)
    y = height // 2 - 50
    for line in wrapped:
        bbox = draw.textbbox((0,0), line, font=title_font)
        w = bbox[2] - bbox[0]
        draw.text((width//2 - w//2, y), line, fill='white', font=title_font)
        y += 70
    
    # Nom de l'auteur
    author_text = f"par {AUTHOR_NAME}"
    bbox = draw.textbbox((0,0), author_text, font=author_font)
    w = bbox[2] - bbox[0]
    draw.text((width//2 - w//2, height - 150), author_text, fill='#ffd966', font=author_font)
    
    # Sauvegarde
    try:
        img.save(abs_path)
        print(f"🖌️ Couverture créée : {abs_path}")
        return abs_path
    except Exception as e:
        print(f"❌ Erreur sauvegarde : {e}")
        # Dernier recours : sauvegarder localement
        fallback = "cover_fallback.jpg"
        img.save(fallback)
        print(f"🔄 Couverture de secours : {fallback}")
        return os.path.abspath(fallback)

def generate_back_cover(book_title, subject, details, num_chapters):
    prompt = f"""
Rédige un texte de quatrième de couverture (200-300 mots) pour le livre "{book_title}".
Sujet : {subject}.
Détails : {details}.
Nombre de chapitres : {num_chapters}.
Style : accrocheur, mystérieux, donne envie de lire.
"""
    try:
        resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        return resp['message']['content']
    except Exception as e:
        print(f"⚠️ Erreur back cover : {e}")
        return f"Plongez dans '{book_title}'. Un univers fascinant à découvrir. Signé {AUTHOR_NAME}."

def create_epub(book_title, chapters_data, back_text, cover_image_path, font_path):
    """Assemble l'EPUB complet avec police, couverture, TOC et 4e de couverture."""
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(book_title)
    book.set_language('fr')
    book.add_author(AUTHOR_NAME)
    book.add_metadata('DC', 'date', datetime.now().isoformat())
    book.add_metadata('DC', 'publisher', 'Editions Astin Java')
    
    # Intégration de la couverture (image)
    if os.path.exists(cover_image_path):
        with open(cover_image_path, 'rb') as img_file:
            book.set_cover("cover.jpg", img_file.read())
    else:
        print("⚠️ Image de couverture introuvable.")
    
    # Intégration de la police OTF
    if os.path.exists(font_path):
        with open(font_path, 'rb') as f:
            font_item = epub.EpubItem(
                file_name=f'fonts/{os.path.basename(font_path)}',
                media_type='application/vnd.ms-opentype',
                content=f.read()
            )
            book.add_item(font_item)
    else:
        print(f"⚠️ Police introuvable : {font_path} – police par défaut.")
    
    # CSS avec la police personnalisée
    css_style = f'''
    @font-face {{
        font-family: "CustomFont";
        src: url(fonts/{os.path.basename(font_path)}) format("opentype");
    }}
    body {{
        font-family: "CustomFont", Georgia, serif;
        margin: 5%;
        text-align: justify;
        line-height: 1.4;
    }}
    h1 {{
        font-family: "CustomFont", Georgia, serif;
        font-size: 1.8em;
        text-align: center;
        margin-top: 20%;
    }}
    h2 {{
        font-family: "CustomFont", Georgia, serif;
        font-size: 1.4em;
        margin-top: 1.5em;
    }}
    .copyright {{
        text-align: center;
        margin-top: 30%;
        font-size: 0.9em;
    }}
    .backcover {{
        margin-top: 20%;
        text-align: center;
        font-style: italic;
    }}
    '''
    css_item = epub.EpubItem(
        file_name='style/main.css',
        media_type='text/css',
        content=css_style
    )
    book.add_item(css_item)
    
    # --- Pages préliminaires ---
    # Page de titre
    title_page = epub.EpubHtml(
        title='Titre',
        file_name='title_page.xhtml',
        lang='fr'
    )
    title_page.content = f'''<html><head><link rel="stylesheet" type="text/css" href="style/main.css"/></head>
    <body>
    <h1>{book_title}</h1>
    <p style="text-align:center;">par {AUTHOR_NAME}</p>
    </body></html>'''
    book.add_item(title_page)
    
    # Page de copyright
    copyright_page = epub.EpubHtml(
        title='Copyright',
        file_name='copyright.xhtml',
        lang='fr'
    )
    copyright_page.content = f'''<html><head><link rel="stylesheet" href="style/main.css"/></head>
    <body>
    <div class="copyright">
    <p>© {datetime.now().year} {AUTHOR_NAME}</p>
    <p>Tous droits réservés.</p>
    <p>Ce livre a été généré partiellement par intelligence artificielle.</p>
    <p>ISBN : {random.randint(1000000000000, 9999999999999)}</p>
    </div>
    </body></html>'''
    book.add_item(copyright_page)
    
    # --- Chapitres ---
    spine_items = ['nav', title_page, copyright_page]
    toc = []
    for idx, (title, content) in enumerate(chapters_data, 1):
        chap_html = epub.EpubHtml(
            title=title,
            file_name=f'chap_{idx:02d}.xhtml',
            lang='fr'
        )
        # Conversion du markdown léger (## ) en HTML
        html_body = content.replace('## ', '<h2>').replace('\n\n', '</p><p>')
        if not html_body.startswith('<h2>'):
            html_body = f'<h2>{title}</h2><p>' + html_body
        html_body += '</p>'
        chap_html.content = f'''<html><head><link rel="stylesheet" href="style/main.css"/></head>
        <body>{html_body}</body></html>'''
        book.add_item(chap_html)
        spine_items.append(chap_html)
        toc.append(chap_html)
    
    # --- Quatrième de couverture ---
    back_page = epub.EpubHtml(
        title='Quatrième de couverture',
        file_name='backcover.xhtml',
        lang='fr'
    )
    back_content = f'''<html><head><link rel="stylesheet" href="style/main.css"/></head>
    <body>
    <div class="backcover">
    <h2>À propos de ce livre</h2>
    <p>{back_text.replace(chr(10), '</p><p>')}</p>
    <p style="margin-top: 3em;">— {AUTHOR_NAME}</p>
    </div>
    </body></html>'''
    back_page.content = back_content
    book.add_item(back_page)
    spine_items.append(back_page)
    toc.append(back_page)
    
    # Table des matières et navigation
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine_items
    
    # Sauvegarde du fichier EPUB
    output_dir_abs = ensure_output_dir()
    epub_path = os.path.join(output_dir_abs, f"{book_title}.epub")
    epub.write_epub(epub_path, book, {})
    print(f"✅ EPUB créé avec succès : {epub_path}")
    return epub_path

def main():
    print("=" * 50)
    print("📚 Studio d'édition Astin Java")
    print("Générateur de livre complet avec IA")
    print("=" * 50)
    
    # Création du dossier de sortie
    ensure_output_dir()
    
    # Saisie utilisateur
    subject, details, num_chapters = ask_book_details()
    # Le titre du livre sera le sujet (capitalisé)
    book_title = subject.capitalize()
    
    # Génération des titres de chapitres
    print("\n🔮 Génération des titres des chapitres...")
    chapter_titles = generate_chapter_titles(subject, num_chapters)
    for i, t in enumerate(chapter_titles, 1):
        print(f"   Titre {i}: {t}")
    
    # Génération du contenu de chaque chapitre
    chapters_data = []
    print("\n📝 Génération du contenu (cela peut prendre plusieurs minutes)...")
    for i, title in enumerate(chapter_titles, 1):
        content = generate_chapter(i, title, subject, details)
        chapters_data.append((title, content))
        time.sleep(1)  # Petite pause pour éviter de surcharger Ollama
    
    # Génération de la quatrième de couverture
    print("\n📖 Génération de la quatrième de couverture...")
    back_text = generate_back_cover(book_title, subject, details, num_chapters)
    
    # Création de l'image de couverture
    cover_path = os.path.join(OUTPUT_DIR, "temp_cover.jpg")
    print("\n🎨 Création de la couverture visuelle...")
    actual_cover_path = create_cover_image(book_title, cover_path)
    
    # Assemblage final de l'EPUB
    print("\n📚 Assemblage du livre électronique...")
    epub_file = create_epub(book_title, chapters_data, back_text, actual_cover_path, FONT_PATH)
    
    print("\n✨ Terminé !")
    print(f"Votre livre '{book_title}' par {AUTHOR_NAME} est prêt.")
    print(f"Fichier EPUB : {epub_file}")
    print("Vous pouvez le tester avec EpubCheck ou l'importer directement dans Google Play Books.")

if __name__ == "__main__":
    # Vérification qu'Ollama est accessible
    try:
        ollama.list()
    except Exception as e:
        print("❌ Ollama n'est pas accessible.")
        print("Assurez-vous qu'Ollama est installé et que le service tourne (commande 'ollama serve' ou 'ollama list').")
        print(f"Détail de l'erreur : {e}")
        sys.exit(1)
    main()