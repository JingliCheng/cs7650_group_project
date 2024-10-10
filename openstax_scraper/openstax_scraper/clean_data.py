import json
import re
from collections import defaultdict

sections_to_exclude = ['figure', 'criticalthinkingquestions', 'reviewquestions', 'os-figure', 'clearup', "linkup", "introduction", "learning objectives"]

with open('/Users/pika/Desktop/cs7650_group_project/openstax_scraper/output.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

cleaned_data = [
    section for section in data
    if section.get('section_name') and isinstance(section['section_name'], str) and section['section_name'].lower() not in sections_to_exclude
]

stopwords = set(["the", "and", "is", "in", "it", "to", "of", "for", "with"])

def clean_text(text):
    text = re.sub(r'\s+', ' ', text) 
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in stopwords])
    return text

def process_question_answer(section_text):
    sentences = section_text.split('answer')
    question = sentences[0].strip()
    answer = None

    if len(sentences) >= 2: 
        answer = sentences[1].strip() 

    return question, answer

grouped_data = defaultdict(list)

for section in cleaned_data:
    if 'section_text' in section and isinstance(section['section_text'], str):
        section['section_text'] = clean_text(section['section_text'])
        
        question, answer = process_question_answer(section['section_text'])
        
        grouped_data[section['chapter_name']].append({
            'question': question,
            'answer': answer if answer else None,
            'section_name': section.get('section_name', ''),
            'textbook_name': section.get('textbook_name', ''),
            'chapter_url': section.get('chapter_url', '')
        })

output_file = '/Users/pika/Desktop/cs7650_group_project/openstax_scraper/grouped_output.json'
with open(output_file, 'w', encoding='utf-8') as grouped_file:
    json.dump(grouped_data, grouped_file, indent=4)

print(f"Grouped data has been saved to '{output_file}'.")


