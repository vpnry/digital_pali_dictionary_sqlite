import re

css_input_file = 'temp_extracted_styles.css'
css_output_done = 'done_parse_dpd.css'


def add_selector(css_string, num):
    # Replace "}" with "}\n" to separate each style block
    css_string = css_string.replace('}', '}\n')

    # Add ".dpn" selector before each style block
    css_string = re.sub(r'^(\S.*)$', r'.dp{} \1'.format(num),
                        css_string, flags=re.MULTILINE)

    # Add ".dpn" selector to group selectors
    css_string = re.sub(r'(\.dp\d+\s*[^\{\},]+\s*)(,\s*[^\{\},]+)', r'\1, .dp{}\2'.format(num),
                        css_string)

    # The above regex will produce an extra ',' like: .dp1 table.freq th, .dp1,table.freq td{vertical-align:middle}
    # Need to work around with the below regex since I could not improve the above regex
    # to: .dp1 table.freq th, .dp1 table.freq td{vertical-align:middle}

    # regex to match ".dp{n}, "
    regex = r'\.dp(\d+),\s*'

    # replace comma and whitespace with space
    css_string = re.sub(regex, r'.dp\1 ', css_string)

    css_string = css_string.strip() + '\n\n'
    css_string = css_string.replace("}\n", ";}\n")

    return css_string


def parse_css(css_input_file=css_input_file):
    # read the inline CSS styles from file
    with open(css_input_file) as f:
        inline_css = f.read()

    # Remove this string. \n is needed for later regex matching
    inline_css = re.sub(
        r'<!doctypehtml><html lang=en><meta charset=utf-8> @charset "utf-8";', '\n', inline_css)

    # extract the CSS styles of z tags and add a selector before each
    z_css = re.findall(r'<z class="dp(\d+)">(.*?)</z>',
                       inline_css, flags=re.DOTALL)
    print("Detected unique styles:", len(z_css))
    z_css_with_selector = [add_selector(css, num) for num, css in z_css]

    # join the CSS styles into a single string
    css_string = '\n'.join(z_css_with_selector)

    # add custom css
    my_app_css = '''/** your custom css */

#dictionary-res { display: none; position: fixed; top: 0px; right: 0%; left: 0%; max-height: 70%; width: auto; padding: 4px; /* border: #5abfde solid 1px; */ border-bottom: orange solid 1.5px; background-color: white !important; overflow-x: scroll; overflow-y: scroll; /* z-index: 999 = appears on top of all other elements on the page.*/ z-index: 999; }

.pword { color: brown; font-weight: bold; text-align: center; font-size: x-large; }

/**
 * The below inline css styles are adapted from 
 * Digital Pāḷi Dictionary
 * Creative Commons Attribution-NonCommercial 4.0 International License
 * https://github.com/digitalpalidictionary/digitalpalidictionary/releases
 */

'''

    css_string = my_app_css.strip() + '\n\n' + css_string.strip()

    with open(css_output_done, 'w') as f:
        f.write(css_string)
        print("[OK] Wrote CSS:", css_output_done)


if __name__ == '__main__':
    parse_css()
