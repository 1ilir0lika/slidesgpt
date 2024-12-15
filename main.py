import os
import requests
import random
from bs4 import BeautifulSoup
import json

def download_image_from_keyword(keyword, save_folder="images"):
    """Scarica l'immagine principale dalla ricerca su Bing. Se fallisce, tenta un'altra immagine."""
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    img_path = os.path.join(save_folder, f"{keyword.replace(' ', '_')}.jpg")
    if os.path.exists(img_path):
        return img_path

    search_url = f"https://www.bing.com/images/search?q={keyword.replace(' ', '+')}"
    response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print(f"Errore nel recupero della pagina di ricerca per la keyword: {keyword}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    # Trova tutti i link alle immagini nei risultati
    img_tags = soup.find_all("a", {"class": "iusc"})
    if not img_tags:
        print(f"Nessuna immagine trovata per la keyword: {keyword}")
        return None

    # Prova a scaricare le immagini una per una
    for index, img_tag in enumerate(img_tags):
        try:
            img_meta = json.loads(img_tag["m"])
            img_url = img_meta.get("murl")
            if not img_url:
                print(f"URL immagine non trovato nei metadati per la keyword: {keyword}")
                continue

            # Scarica l'immagine
            img_response = requests.get(img_url)
            if img_response.status_code == 200:
                img_file_path = os.path.join(save_folder, f"{keyword.replace(' ', '_')}_{index}.jpg")
                with open(img_file_path, "wb") as img_file:
                    img_file.write(img_response.content)
                print(f"Immagine salvata: {img_file_path}")
                return img_file_path
            else:
                print(f"Errore nel download dell'immagine da URL: {img_url}")
        except Exception as e:
            print(f"Errore durante il download dell'immagine: {e}")

    print(f"Nessuna immagine valida trovata per la keyword: {keyword}")
    return None


def slide_configs(slide, is_first_slide=False, is_last_slide=False, background=None):
    """Genera la configurazione per una slide."""
    lines = []
    if is_first_slide:
        lines = [
            "---\n",
            "title: \"slidesgpt\"\n",
            f"background: {background}\n",
            "theme: seriph \n",
            "class: text-center \n",
            "transition: slide-left\n",
            "---\n"
        ]
    else:
        n_images = sum(1 for line in slide if line.startswith("image: "))
        rand = random.randint(0, 10)
        image_layout = "image-right" if rand > 5 else "image-left"
        layout = image_layout if n_images > 0 else "center"
        lines.append(f"layout: {layout}\n")
        if n_images > 0:
            for line in slide:
                if line.startswith("image: "):
                    keyword = line[len("image: "):].strip()
                    img_path = download_image_from_keyword(keyword)
                    if img_path:
                        lines.append(f"image: {img_path}\n")
        lines.append("---\n")
    return lines

filename = "slides.md"
output_filename = "slides_processed.md"

# Leggi il contenuto del file originale
with open(filename, "r") as f:
    content = f.readlines()

# Estrai la keyword per il background dalla prima riga
background_keyword = content[0].strip().replace("background:", "").strip()
background_image = download_image_from_keyword(background_keyword)
content = content[1:]  # Elimina la prima riga

# Dividi il contenuto in slide
slides = []
current_slide = []

for line in content:
    if line.strip() == "---":
        if current_slide:
            slides.append(current_slide)
            current_slide = []
    else:
        current_slide.append(line.strip())
if current_slide:
    slides.append(current_slide)

# Scrivi il nuovo file con il background e configurazioni aggiornate
with open(output_filename, "w") as out_file:
    for i, slide in enumerate(slides):
        is_first_slide = (i == 0)
        is_last_slide = (i == len(slides) - 1)
        slide_config = slide_configs(
            slide,
            is_first_slide=is_first_slide,
            is_last_slide=is_last_slide,
            background=background_image if is_first_slide else None
        )
        out_file.writelines(slide_config)
        # Scrivi il contenuto della slide senza le righe `image:`
        for line in slide:
            if not line.startswith("image: "):
                out_file.write(f"{line}\n")
        out_file.write("---\n")

    # Aggiungi una slide di ringraziamento alla fine
    end_slide = [
        "layout: end\n",
        "transition: zoom\n",
        "---\n",
        "# Grazie per l'attenzione\n",
        "**Domande?**\n"
    ]
    out_file.writelines(end_slide)

print(f"File processato salvato come {output_filename}")
