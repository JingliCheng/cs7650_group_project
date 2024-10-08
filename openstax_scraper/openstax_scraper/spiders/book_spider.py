import scrapy
    

class BookSpider(scrapy.Spider):
    name = "textbook"
    start_urls = [
        'https://openstax.org/books/principles-economics-3e/pages/1-introduction',
        'https://openstax.org/books/principles-microeconomics-3e/pages/1-introduction',
        'https://openstax.org/books/principles-macroeconomics-3e/pages/1-introduction',
    ]

    def parse(self, response):
        current_url = response.url
        base_url = current_url[:-len(current_url.split('/')[-1])]
        # Extract all links to chapters from the TOC page
        chapter_links = response.css('ol a.styled__ContentLink-sc-18yti3s-1::attr(href)').getall()
        for link in chapter_links[:]:
            # print(link)
            # Follow each link (assuming it's relative to the base URL)
            if 'key-terms' in link:
                yield response.follow(link, self.parse_key_terms)
            elif 'key-concepts-and-summary' in link:
                yield response.follow(link, self.parse_key_concepts_and_summary)
            elif 'self-check-questions' in link:
                yield response.follow(link, self.parse_self_check_questions)
            elif 'review-questions' in link:
                yield response.follow(link, self.parse_review_questions)
            elif 'critical-thinking-questions' in link:
                yield response.follow(link, self.parse_critical_thinking_questions)
            elif 'preface' in link:
                continue
            elif 'introduction' in link:
                yield response.follow(link, self.parse_introduction)
            else:
                yield response.follow(link, self.parse_chapter)

    def parse_preface(self, response):
        pass

    def parse_introduction(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]

        content = response.css('div.introduction')
        chapter_text = content.css('::text').getall()
        section_name = 'introduction'

        chapter_text = ''.join(chapter_text)
        filtered_text = chapter_text

        yield {
                'section_name': section_name,
                'section_text': filtered_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }


    def parse_key_terms(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[id="main-content"]')
        chapter_text = content.css('::text').getall()

        chapter_text = ''.join(chapter_text)
        yield {
                'section_name': section_name,
                'section_text': chapter_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }


    def parse_key_concepts_and_summary(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[id="main-content"]')
        chapter_text = content.css('::text').getall()

        chapter_text = ''.join(chapter_text)
        yield {
                'section_name': section_name,
                'section_text': chapter_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }


    def get_answer(self, response):
        question_text = response.meta['question_text']
        data_page_fragment = response.meta['data_page_fragment']

        if data_page_fragment:
            # Use the data_page_fragment to find the specific part of the page with the answer
            answer_selector = response.css(f'div[id="{data_page_fragment}"]')
            answer_text = answer_selector.css('::text').getall()  # Assuming answer is in a <p> tag within the fragment
            answer_text = ''.join(answer_text)
            # print('answer_text: \n\n', answer_text)
        else:
            answer_text = 'Answer not found'

        qa_pair = f"Question: {question_text} Answer: {answer_text}"
        yield {
            'section_name': 'self-check-questions',
            'section_text': qa_pair,
            'chapter_name': response.meta['chapter_name'],
            'textbook_name': response.meta['textbook_name'],
            'chapter_url': response.meta['chapter_url']
        }

    def parse_self_check_questions(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]

        questions = response.css('div[data-type="problem"]')
        for question in questions:
            question_text = question.css('::text').getall()
            question_text = ''.join(question_text)
            answer_link = question.css('::attr(href)').get()
            if answer_link:
                data_page_fragment = question.css('::attr(data-page-fragment)').get()
                # get the answer from the url and local it with the data_page_fragment
                # print(answer_link)
                # print(question_text)
                yield response.follow(answer_link, self.get_answer, meta={
                        'question_text': question_text,
                        'data_page_fragment': data_page_fragment,
                        'chapter_name': chapter_name,
                        'textbook_name': textbook_name,
                        'chapter_url': chapter_url
                    }, dont_filter=True)


    def parse_review_questions(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[data-type="problem"]')
        chapter_text = content.css('::text').getall()

        chapter_text = ''.join(chapter_text)
        yield {
                'section_name': section_name,
                'section_text': chapter_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }
    

    def parse_critical_thinking_questions(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]
        section_name = ''.join(chapter_name.split('-')[1:])

        content = response.css('div[data-type="problem"]')
        chapter_text = content.css('::text').getall()

        chapter_text = ''.join(chapter_text)
        yield {
                'section_name': section_name,
                'section_text': chapter_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }


    def parse_section(self, content, chapter_url, section_name=None):
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]

        sections_text = content.css('::text').getall()
        section_text = ''.join(sections_text)
        if content.css('h2[data-type="title"]::text').get():
            section_name = content.css('h2[data-type="title"]::text').get()
            # section_text = section_text[len(section_name):]
        filtered_text = section_text

        SPECIAL_SECTIONS = ['bringhome', 'clearup', 'linkup']
        IMAGE_SECTIONS = ['os-figure']

        for s in SPECIAL_SECTIONS + IMAGE_SECTIONS:
            for local_content in content.css(f'div.{s}'):
                special_text = ''.join(local_content.css('::text').getall())
                filtered_text = filtered_text.replace(special_text, '')
                yield {
                    'section_name': s,
                    'section_text': special_text,
                    'chapter_name': chapter_name,
                    'textbook_name': textbook_name,
                    'chapter_url': chapter_url
                }
        
        yield {
                'section_name': section_name,
                'section_text': filtered_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }


    def parse_chapter(self, response):
        chapter_url = response.url
        chapter_name = chapter_url.split('/')[-1]
        textbook_name = chapter_url.split('/')[4]

        content = response.css('div.chapter-content-module')
        chapter_text = content.css('::text').getall()
        section_name = None

        if content.css('h2[data-type="title"]::text').get():
            section_name = content.css('h2[data-type="title"]::text').get()
            # add a newline after the section name
            chapter_text = chapter_text[:len(section_name)] + ['\n'] + chapter_text[len(section_name):]

        chapter_text = ''.join(chapter_text)
        filtered_text = chapter_text

        # Delete sections from chapter text
        sections = content.css('div.chapter-content-module > section')
        sections_text = []
        for section in sections:
            temp_section_text_nodes = section.css('::text').getall()
            temp_section_text = ''.join(temp_section_text_nodes)
            sections_text.append(temp_section_text)
        # print(len(sections))
        # print(len(sections_text))

        for section_text in sections_text:
            filtered_text = filtered_text.replace(section_text, '')
        
        # Delete special cases, e.g. Figures, 'bringhome', 'clearup', 'linkup'
        SPECIAL_SECTIONS = ['bringhome', 'clearup', 'linkup']
        IMAGE_SECTIONS = ['os-figure']

        for s in SPECIAL_SECTIONS + IMAGE_SECTIONS:
            for local_content in content.css(f'div.chapter-content-module > div.{s}'):
                special_text = ''.join(local_content.css('::text').getall())
                filtered_text = filtered_text.replace(special_text, '')
                yield {
                    'section_name': s,
                    'section_text': special_text,
                    'chapter_name': chapter_name,
                    'textbook_name': textbook_name,
                    'chapter_url': chapter_url
                }

        yield {
                'section_name': section_name,
                'section_text': filtered_text,
                'chapter_name': chapter_name,
                'textbook_name': textbook_name,
                'chapter_url': chapter_url
            }
        
        for block in content.css('div.chapter-content-module > section'):
            yield from self.parse_section(block, chapter_url, section_name="learning obj")
            # print('\n=====================\n')