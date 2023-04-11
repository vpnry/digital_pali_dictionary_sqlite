import os
import sqlite3


def stardict_tab_to_sqlite3(tab_file: str) -> None:
    # Generated with the support of ChatGPT OpenAI
    # 13 Mar 2023

    # Check if the dictionary.db file exists and delete it if it does
    if os.path.exists('dictionary.db'):
        os.remove('dictionary.db')
        print('The dictionary.db file exists, deleted')

    # Connect to a SQLite database
    conn = sqlite3.connect('dictionary.db')

    # Create a table named "dictionary" with columns "idx", "word", and "defi"
    conn.execute('''CREATE TABLE IF NOT EXISTS dictionary
                (idx INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                defi TEXT NOT NULL);''')

    # Read the tab-delimited file and insert the data into the "dictionary" table
    with open(tab_file, 'r', encoding='utf-8') as f:
        batch_size = 50000
        batch = []
        counter = 0
        for line in f:
            # Split the line into columns "word" and "defi"
            word, defi = line.strip().split('\t', 1)
            # Add the data to the batch
            batch.append((word, defi))
            # If the batch size is reached, insert the data into the "dictionary" table
            if len(batch) == batch_size:
                counter += 1
                print("Inserting data into", batch_size * counter)
                conn.executemany(
                    "INSERT INTO dictionary (word, defi) VALUES (?, ?)", batch)
                batch = []
        # Insert the remaining data (if any) into the "dictionary" table
        if batch:
            conn.executemany(
                "INSERT INTO dictionary (word, defi) VALUES (?, ?)", batch)

    # Commit changes and close the connection to the database
    conn.commit()
    conn.close()

    # Print the size of the dictionary.db file in MB
    db_size_mb = os.path.getsize('dictionary.db') / (1024**2)
    print(f"The size of the dictionary.db file is ~ {db_size_mb:.2f} MB")
    print("The function stardict_tab_to_sqlite3 is done")


if __name__ == '__main__':
    stardict_tab_to_sqlite3("tabfile.txt")
