"""Convert the DPD Goldendict data into a Sqlite db

1. Remove inline CSS styles, script
2. Only keep Roman pali script (Otherwise the database file size will be VERY big)
2. Handle synonyms

"""

import os
import re
import sqlite3
import subprocess
import sys
import zipfile
import requests
from parse_dpd_css import parse_css


PALI_ROMAN_CHARS = r'[ĀĪŪṀṂṆḌḶṚṢŚÑṄāīūṁṃṇḍḷṛṣśñṅA-Za-z]'

raw_extracted_styles = 'temp_extracted_styles.css'


def is_pyglossary_installed():
    try:
        # Check if PyGlossary is available
        subprocess.check_output(['pyglossary', '-h'])
        print("PyGlossary is already installed!")
    except:
        # If PyGlossary is not available, ask user for confirmation to install
        answer = input(
            "PyGlossary is not installed. Do you want to install it? (y/n) ")
        if answer.lower() == 'y':
            # Install PyGlossary using pip3
            subprocess.run(['pip3', 'install', 'pyglossary'])
            print("PyGlossary has been installed!")
        else:
            print(
                "PyGlossary is required for this script to run. Please install it manually.")
            print("The script will stop here...")
            sys.exit()


def download_dpd_zip():
    download_guide = '''
        dpd.zip (Goldendict data) is NOT available locally.
        Check for the latest release here https://github.com/digitalpalidictionary/digitalpalidictionary/releases

        A link for dpd.zip will be something like: https://github.com/digitalpalidictionary/digitalpalidictionary/releases/download/yyyy-mm-dd/dpd.zip
    '''

    # Check if dpd.zip exists locally
    if os.path.exists('dpd.zip'):
        print('dpd.zip is already available locally.')
    else:
        # Prompt user to enter URL to download zip file
        print(download_guide)
        url = input('Paste the URL of dpd.zip to download: ')

        # Download zip file from URL
        response = requests.get(url)
        with open('dpd.zip', 'wb') as f:
            f.write(response.content)
            print('dpd.zip is already downloaded.')

    # Extract zip file
    with zipfile.ZipFile('dpd.zip', 'r') as zip_ref:
        print('Extracting dpd.zip...')
        zip_ref.extractall('extracted')

    # Install PyGlossary if needed
    is_pyglossary_installed()

    # Run PyGlossary command
    print('Converting dpd to tabfile dpd.txt. It will take time, please wait...')
    print('You can ignore the [INFO] message from pyglossary')

    command = ['pyglossary', 'extracted/dpd/dpd.ifo', 'dpd.txt',
               '--read-format=Stardict', '--write-format=Tabfile']
    subprocess.run(command)

    # Clean up extracted files
    # os.system('rm -r extracted')
    # os.remove('dpd.zip')


def remove_title_and_body_tags(text: str) -> str:
    cleaned_text = text.replace(
        '<title>Digital Pāḷi Dictionary</title><body>', '')
    cleaned_text = cleaned_text.replace('<body>', '')
    return cleaned_text.strip()


def extract_and_remove_script_tag(defi: str) -> tuple:
    match = re.search(r'<script>.*?</script>', defi)
    script_tag = ''

    if match:
        script_tag = match.group()
        defi = defi.replace(script_tag, '')

    return (remove_title_and_body_tags(defi), script_tag)


def filter_latin_words(words: list) -> list:
    return [word for word in words if re.search(PALI_ROMAN_CHARS, word)]


def dpd_to_sqlite_main(tab_file: str = "dpd.txt") -> None:

    download_dpd_zip()

    print("Generating Sqlite3: dictionary.db")
    print("It will take a while....")

    if os.path.exists('dictionary.db'):
        os.remove('dictionary.db')
        print('The dictionary.db file exists, deleted')

    conn = sqlite3.connect('dictionary.db')

    conn.execute('''CREATE TABLE IF NOT EXISTS dictionary
                (idx INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                defi TEXT NOT NULL);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS synonyms
                (synonym TEXT NOT NULL,
                word TEXT NOT NULL,
                PRIMARY KEY (synonym, word));''')

    with open(tab_file, 'r', encoding='utf-8') as f:
        batch_size = 10000
        batch = []
        style_tags = []
        style_counter = 0
        batch_counter = 0

        for line in f:
            words, defi = line.strip().split('\t', 1)
            words = words.strip().split('|')

            word = words[0].strip()
            word = re.sub(r'^[\W\d_]+|[\W\d_]+$', '', word)
            word = word.lower().strip()

            if '</style>' in defi:
                defi_parts = defi.strip().split('</style>', 1)
                defi = defi_parts[1]

                defi, script_txt = extract_and_remove_script_tag(defi)
                css = defi_parts[0].strip()

                if script_txt not in style_tags:
                    style_tags.append(script_txt)
                    print(script_txt)

                if css not in style_tags:
                    style_counter += 1
                    defi = f'<section class="dp{style_counter}">{defi}</section>'

                    style_tags.append('Start')
                    style_tags.append(
                        f'<z class="dp{style_counter}">{css.strip()}</z>')
                    style_tags.append(css)
                    style_tags.append('End')
                else:
                    defi = f'<section class="dp{style_counter}">{defi}</section>'

            batch.append((word, defi.strip()))

            # Remove other scripts (otherwise the database file size will be VERY big)
            words = filter_latin_words(words)
            for n in range(len(words)):
                if n == 0:
                    continue
                conn.execute('''INSERT OR IGNORE INTO synonyms (synonym, word)
                VALUES (?, ?)''', (words[n].lower().strip(), word))

            if len(batch) == batch_size:
                batch_counter += 1
                print("Inserting data into dictionary",
                      batch_size * batch_counter)
                conn.executemany(
                    "INSERT INTO dictionary (word, defi) VALUES (?, ?)", batch)
                batch = []

        if batch:
            conn.executemany(
                "INSERT INTO dictionary (word, defi) VALUES (?, ?)", batch)

    conn.commit()
    conn.close()

    db_size_mb = os.path.getsize('dictionary.db') / (1024**2)
    print(f"The size of the dictionary.db file is ~ {db_size_mb:.2f} MB")

    os.system("zip dictionary.zip dictionary.db")
    zip_size_mb = os.path.getsize('dictionary.zip') / (1024**2)

    print(f"The size of the dictionary.db file is ~ {zip_size_mb:.2f} MB")

    with open(raw_extracted_styles, 'w', encoding='utf-8') as css_file:
        css_content = '\n\n'.join(style_tags).replace('\\n', ' ')
        css_content = css_content.replace(
            '<!DOCTYPE html>', '').replace('<meta charset="utf-8">', ' ')
        css_content = css_content.replace('<style>', ' ')
        css_file.write(css_content)

        print("\nParsing the css file...")
        parse_css(raw_extracted_styles)
    print("\nDone all!")


if __name__ == '__main__':
    dpd_to_sqlite_main()
