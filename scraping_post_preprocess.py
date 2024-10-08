import json
from datetime import datetime

VOLUNTEER_ID= "2052"
LOCATION = "Atlanta, USA"
INPUT_FILE = 'openstax_scraper/output.json'
OUTPUT_FILE = 'openstax_scraper/processed_output.json'


def process_text(text):
    """
    Process the raw text to ensure it's grammatically readable.
    This function can be expanded based on specific rules or libraries like nltk.
    """
    # Basic processing: split into sentences, strip whitespace, and remove empty sentences.
    # sentences = [sentence.strip() for sentence in text.split('.') if sentence.strip()]
    # output = ' '.join(sentences)
    output = text
    return output

def reformat_data(input_file, output_file, volunteer_id, location):
    with open(input_file, 'r', encoding='UTF-8') as file:
        data = json.load(file)

    new_data = []
    for entry in data:
        # Process the section text to be grammatically readable
        processed_text = process_text(entry['section_text'])

        # Build the new JSON object
        new_entry = {
            "text": processed_text,
            "metadata": {
                "date downloaded": datetime.now().strftime("%Y-%m-%d"),
                "site url": entry['chapter_url'],
                "extra data": {
                    "chapter": entry['chapter_name'],
                    "section": entry['section_name'],
                    "textbook": entry['textbook_name']
                }
            },
            "volunteer id": volunteer_id,
            "location": location
        }
        new_data.append(new_entry)

    # Output the formatted data
    with open(output_file, 'w') as outfile:
        for dict_data in new_data:
            json_line = json.dumps(dict_data)
            outfile.write(json_line + '\n')

if __name__ == '__main__':
    reformat_data(INPUT_FILE, OUTPUT_FILE, VOLUNTEER_ID, LOCATION)