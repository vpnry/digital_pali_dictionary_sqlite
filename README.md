## Info

This Python script converts the **dpd.zip** file (Goldendict data) from [Digital Pali Dictionary](https://github.com/digitalpalidictionary/digitalpalidictionary/releases), into an Sqlite3 database file (**dictionary.db** ~1.x GB).

## How to use

- System requirements: python3, zip (` sudo apt install zip`), pyglossary (`pip3 install -U pyglossary`)

- Run the script and answer its prompts:

```bash

python3 dpd_to_sqlite.py

```

---
## Dev Notes

### 0. Only Roman Pali

All word entries are in Romanized Pali only, with other Pali scripts stripped out to prevent excessive file size in the database.

```python

PALI_ROMAN_CHARS = r'[ĀĪŪṀṂṆḌḶṚṢŚÑṄāīūṁṃṇḍḷṛṣśñṅA-Za-z]'

```

### 1. Inline CSS styles

It removes inline CSS styles and JavaScript snippets present in the dicionary, and compiles them into a separate file named `temp_extracted_styles.css`. This step helps to reduce the size of the output database file.

Each word definition will be wrapped in `<section class="dp{number}"> definition here </section>` where number is from 1 to n.

It also attempts to parse `temp_extracted_styles.css` and generates the final output file `done_parse_dpd.css`. Please note that it is necessary to review these files **manually** as the inline CSS may undergo changes in future DPD releases. 


### 2. Synonyms

Synonyms are stored in a separate table within the database. 

### 3. SQlite3 db structure of the output dictionary.db

```python3
conn.execute('''CREATE TABLE IF NOT EXISTS dictionary
                (idx INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                defi TEXT NOT NULL);''')

conn.execute('''CREATE TABLE IF NOT EXISTS synonyms
                (synonym TEXT NOT NULL,
                word TEXT NOT NULL,
                PRIMARY KEY (synonym, word));''')
```

### 4. Final check

After running the script, you should re-check `done_parse_dpd.css` and `dictionary.db` before integrating them into your application.

You can use this GUI [DB Browser for SQLite](https://sqlitebrowser.org/) to view the `dictionary.db` file and ensure that the data has been properly formatted and organized. 

## Example usage

The following Kotlin code snippet provides an example of how to perform a lookup in the database. 

```kotlin

fun getDefinition(word: String): String {
    // query SQLite database and return definition(s) for word or its synonyms
    val synonymsCursor = db.query(
        "synonyms",
        arrayOf("word"),
        "synonym=?",
        arrayOf(word),
        null,
        null,
        null
    )

    // Add the original word to the list of possible words
    val words = mutableListOf(word)
    with(synonymsCursor) {
        while (moveToNext()) {
            words.add(getString(getColumnIndexOrThrow("word")))
        }
    }

    synonymsCursor.close()

    // query dictionary table for definitions of all possible words
    val definitions = mutableListOf<String>()
    val args = words.joinToString(separator = ",") { "?" }
    val cursor = db.query(
        "dictionary",
        arrayOf("defi"),
        "word IN ($args)",
        words.toTypedArray(),
        null,
        null,
        null
    )

    with(cursor) {
        while (moveToNext()) {
            definitions.add(getString(getColumnIndexOrThrow("defi")))
        }
    }

    cursor.close()

    // combine definitions into a single string
    // return definitions.joinToString(separator = "")

    var counter = 1
    // add number counter if there are multiple definitions
    // combine definitions into a single string with counter inserted after <section class="dp{NUMBER}">

    return if (definitions.size > 1) {
        definitions.joinToString(separator = "\n\n") { def ->
            def.replace(Regex("<section class=\"dp\\d+\">")) { matchResult ->
                "${matchResult.value}${counter++}. "
            }
        }
    } else {
        definitions.joinToString(separator = "")
    }

}

```

## Attributions

- [Digital Pāḷi Dictionary](https://github.com/digitalpalidictionary/digitalpalidictionary/releases) is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License](http://creativecommons.org/licenses/by-nc/4.0/)

- Many code snippets here are generated with [ChatGPT](https://chat.openai.com/chat)
