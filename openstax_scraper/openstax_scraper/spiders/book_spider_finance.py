import scrapy

class BookSpider(scrapy.Spider):
    name = "finance"
    start_urls = [
        'https://openstax.org/books/principles-finance/pages/1-why-it-matters',
    ]

    def parse(self, response):
        current_url = response.url
        base_url = current_url[:-len(current_url.split('/')[-1])]
        # Extract all links to chapters from the TOC page
        chapter_links = response.css('ol a.styled__ContentLink-sc-18yti3s-1::attr(href)').getall()
        for link in chapter_links[:]:
            if 'key-terms' in link:
                yield response.follow(link, self.parse_key_terms)
            elif 'summary' in link:
                yield response.follow(link, self.parse_summary)
            elif 'multiple-choice' in link:
                yield response.follow(link, self.parse_multiple_choice)
            elif 'review-questions' in link:
                yield response.follow(link, self.parse_review_questions)
            elif 'problems' in link:
                yield response.follow(link, self.parse_problems)
            # elif 'preface' in link:
            #     continue
            # elif 'why-it-matters' in link:
            #     yield response.follow(link, self.parse_why_it_matters)
            else:
                yield response.follow(link, self.parse_chapter)



    def parse_key_terms(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        # Target the key terms section
        content = response.css('div[id="main-content"]')

        # Extract all <dt> and <dd> elements within the content
        terms = content.css('dl dt::text').getall()  # Extract terms
        definitions = content.css('dl dd::text').getall()  # Extract definitions

        key_terms = []
        for term, definition in zip(terms, definitions):
            key_terms.append({
                'term': term.strip(),
                'definition': definition.strip(),
            })

        chapter_text = content.css('::text').getall()
        chapter_text = ''.join(chapter_text)

        yield {
            'section_name': section_name,
            'section_text': chapter_text,
            'chapter_name': chapter_name,
            'textbook_name': textbook_name,
            'chapter_url': chapter_url,
            'key_terms': key_terms,  # Include key terms in the output
        }


    def parse_summary(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[id="main-content"]')

        # Find all sections containing questions and answers
        sections = content.css('section.section-summary')

        questions_and_answers = []

        # Loop through each section to extract the question and its corresponding answer
        for section in sections:
            # Extract the question (from <h2> tag)            
            question = section.css('h2::text').get()
            # Extract the answer (from the <p> tag after the question)
            answer = section.css('p::text').get()
            # Add the extracted question and answer as a pair to the list
            if question and answer:
                questions_and_answers.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })

        # Join chapter text as before
        chapter_text = content.css('::text').getall()
        chapter_text = ''.join(chapter_text)

        # Yield the extracted questions and answers, along with other chapter details
        yield {
            'section_name': section_name,
            'questions_and_answers': questions_and_answers,
            'chapter_text': chapter_text,
            'chapter_name': chapter_name,
            'textbook_name': textbook_name,
            'chapter_url': chapter_url
        }


    def parse_multiple_choice(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[id="main-content"]')

        # Extract all question containers
        question_containers = content.css('div.os-problem-container')

        questions_with_choices = []

        # Loop through each question container to extract the question and choices
        for container in question_containers:
            # Extract the question (from <div class="question-stem">)
            question = container.css('div[data-type="question-stem"]::text').get()

            # Extract the choices (from <li> tags inside <ol>)
            choices = container.css('li[data-type="question-answer"] div[data-type="answer-content"]::text').getall()

            # Add the question and corresponding choices to the list
            if question and choices:
                questions_with_choices.append({
                    'question': question.strip(),
                    'choices': [choice.strip() for choice in choices]
                })

        # Join chapter text as before
        chapter_text = content.css('::text').getall()
        chapter_text = ''.join(chapter_text)

        # Yield the extracted questions with choices, along with other chapter details
        yield {
            'section_name': section_name,
            'questions_with_choices': questions_with_choices,
            'chapter_text': chapter_text,
            'chapter_name': chapter_name,
            'textbook_name': textbook_name,
            'chapter_url': chapter_url
        }



    def parse_review_questions(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[id="main-content"]')

        # Extract all question containers
        question_containers = content.css('div.os-problem-container')

        questions = []

        # Loop through each question container to extract the question text
        for container in question_containers:
            # Extract the question (from <div class="question-stem">)
            question = container.css('div[data-type="question-stem"]::text').get()

            # Add the question to the list if it exists
            if question:
                questions.append({
                    'question': question.strip()
                })

        # Join chapter text as before
        chapter_text = content.css('::text').getall()
        chapter_text = ''.join(chapter_text)

        # Yield the extracted questions, along with other chapter details
        yield {
            'section_name': section_name,
            'questions': questions,
            'chapter_text': chapter_text,
            'chapter_name': chapter_name,
            'textbook_name': textbook_name,
            'chapter_url': chapter_url
        }
    

    def parse_problems(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[id="main-content"]')

        # Extract all exercise-question containers
        question_containers = content.css('div[data-type="exercise-question"]')

        questions = []

        # Loop through each question container to extract the question text
        for container in question_containers:
            # Extract the question number (from <span class="os-number">)
            question_number = container.css('span.os-number::text').get()

            # Extract the question (from <div class="question-stem">)
            question = container.css('div[data-type="question-stem"]::text').get()

            # Add the question number and text to the list
            if question and question_number:
                questions.append({
                    'question_number': question_number.strip(),
                    'question': question.strip()
                })

        # Join chapter text as before
        chapter_text = content.css('::text').getall()
        chapter_text = ''.join(chapter_text)

        # Yield the extracted questions, along with other chapter details
        yield {
            'section_name': section_name,
            'questions': questions,
            'chapter_text': chapter_text,
            'chapter_name': chapter_name,
            'textbook_name': textbook_name,
            'chapter_url': chapter_url
        }


    def parse_chapter(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]

        content = response.css('div.chapter-content-module')
        structured_content = []
        for element in content.xpath('./*'):  # Only get direct children of the div
            tag = element.root.tag  # Get the tag name
            text = element.xpath('.//text()').getall()  # Get the text inside the tag, including nested elements
            
            if text:  # If there is any text inside the tag
                structured_content.append(f"<{tag}> {''.join(text).strip()} </{tag}>")

        # Join the structured content into a single string
        html_structure = '\n'.join(structured_content)
        section_name = None

        yield {
                'section_name': section_name,
                'section_text': html_structure,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }
