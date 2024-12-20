import json
import openai
import random
import copy
from typing import List, Dict, Any, Tuple

class KeyPointDistorter:
    Index_list = 'ABCDEFGHIJK'

    def __init__(self, client, model: str = "gpt-4o-mini", temperature: float = 0.0, seed: int = None):
        """Initialize the KeyPointDistorter with OpenAI client and parameters.
        Args:
            client: openai.OpenAI or openai.AzureOpenAI
            model: model name
            temperature: temperature for the model
        """
        self.client = client
        self.model = model
        self.temperature = temperature
        self.Index_map = {c: i for i, c in enumerate(self.Index_list)}
        self.seed = seed
        if self.seed:
            random.seed(self.seed)
        self.prompt_results = {}

    def reset_prompt_results(self):
        self.prompt_results = {}

    def store_prompt_result(self, prompt: str, response: str, step_name: str):
        """Store the prompt and response for each step."""
        if step_name not in self.prompt_results:
            self.prompt_results[step_name] = []
        self.prompt_results[step_name].append({'prompt': prompt, 'response': response})

    def extract_keypoints(self, question: Dict[str, str]) -> Dict[str, Any]:
        """Extract keypoints from the given question and answer."""
        # TODO: keypoints should be isolated from the others
        prompt = f"""
        Question: {question['question']}
        Gold Answer: {question['answer']}
        Your task: Think about the question and understand the answer first, \
then extract complete bullet points that are key keypoints based on the answer \
for rebuilding the answer from scratch for the same question, more keypoints will be helpful. At leat find 5 keypoints. \
In the output json, keypoints' name should be different to serve as a key. If two keypoints are the same, name the second \
one with a different name.
        Return a JSON object in this exact format:
                {{
                    "Analysis": "Analysis of the question, answer, and the keypoints",
                    "Keypoints": [
                        {{"keypoint": "string", "detail": "string"}},
                        {{"keypoint": "string", "detail": "string"}},
                        ... and so on, until all keypoints are covered.
                    ]
                }}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        output = json.loads(response.choices[0].message.content)
        self.store_prompt_result(prompt, output, "extract_keypoints")
        return output

    def distort_keypoint(self, question: str, keypoint: Dict[str, str], other_keypoints: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a misleading version of a specific keypoint."""
        prompt = f"""
        Task: For the selected keypoint, what is a misleading direction of the keypoint for the question. \
Modify or rewrite the keypoint to create a misleading keypoint. Keep other keypoints the same.
        Question: {question}
        Selected Keypoint: {keypoint['keypoint']}. Description: {keypoint['detail']}
        """
        
        for other_keypoint in other_keypoints:
            prompt += f"Other Keypoint: {other_keypoint['keypoint']}. Description: {other_keypoint['detail']}\n"

        prompt += """
        Return a JSON object in this exact format:
                {
                    "analysis_1": "How the misleading keypoint can be created. Think step by step.",
                    "analysis_2": "Think deeper.",
                    "new_keypoint": "string",
                    "new_keypoint_detail": "string",
                    "old_keypoint": "string"
                    "old_keypoint_detail": "string"
                }
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        output = json.loads(response.choices[0].message.content)
        output['real_old_keypoint'] = keypoint['keypoint']
        self.store_prompt_result(prompt, output, "distort_keypoint")
        return output
    
    def generate_true_answer(self, question: str, keypoints: List[Dict[str, str]]) -> str:
        """Generate an answer based on the given keypoints."""
        keypoints_prompt = "Keypoints:\n"
        for keypoint in keypoints:
            keypoints_prompt += f"{keypoint['keypoint']}: {keypoint['detail']}\n"

        prompt = f"""
        Task: Generate a concise and unified answer to the given question using the provided keypoints as guidelines.
- Treat the directions as guiding principles, not as rigid rules.
- Combine all elements into a single, cohesive paragraph.
- Do not overanalyze or include your thought process.
- Avoid summarizing at the end.

        Question: {question}
        {keypoints_prompt}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        output = response.choices[0].message.content
        self.store_prompt_result(prompt, output, "generate_true_answer")
        return output

    def generate_mislead_answer(self, question: str, distorted_keypoint: Dict[str, str], other_keypoints: List[Dict[str, str]]) -> str:
        """Generate an answer based on the given keypoints."""
        main_keypoint_prompt = f"Main Keypoint: \n{distorted_keypoint['new_keypoint']}: {distorted_keypoint['new_keypoint_detail']}\n"
        other_keypoints_prompt = "Other Keypoints:\n"
        for keypoint in other_keypoints:
            other_keypoints_prompt += f"{keypoint['keypoint']}: {keypoint['detail']}\n"

        prompt = f"""
        Task: Generate a concise and unified answer to the given question using the provided keypoints as guidelines.
- Follow the main keypoint strictly.
- Adjust or modify other keypoints only if they conflict with the main keypoint.
- Treat the directions as guiding principles, not as rigid rules.
- Combine all elements into a single, cohesive paragraph.
- Do not overanalyze or include your thought process.
- Avoid summarizing at the end.

        Question: {question}
        {main_keypoint_prompt}
        {other_keypoints_prompt}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        output = response.choices[0].message.content
        self.store_prompt_result(prompt, output, "generate_mislead_answer")
        return output

    def process_question(self, question: Dict[str, str], num_keypoints: int = 3) -> List[str]:
        """Process a question and generate multiple versions with changed keypoints."""
        # Extract keypoints
        extracted = self.extract_keypoints(question)
        # print(f'number of keypoints: {len(extracted["Keypoints"])}')
        # Select random keypoints to modify
        random_keypoints = random.sample(extracted['Keypoints'], k=num_keypoints)
        answers = []

        # Generate original answer
        original_answer = self.generate_true_answer(question['question'], extracted['Keypoints'])
        answers.append(original_answer)

        # Generate new versions with distorted keypoints
        count = 0
        for keypoint in random_keypoints:
            # print(count)
            other_keypoints = [f for f in extracted['Keypoints'] if f != keypoint]
            # Distort the keypoint
            distorted = self.distort_keypoint(question['question'], keypoint, other_keypoints)
            # Create new keypoint set
            other_keypoints = copy.deepcopy(extracted['Keypoints'])
            for kp in other_keypoints:
                if kp['keypoint'] == distorted['real_old_keypoint']:
                    other_keypoints.remove(kp)
                    count += 1
            # Generate answer with new keypoints
            answer = self.generate_mislead_answer(question['question'], distorted, other_keypoints)
            answers.append(answer)
        
        assert count == num_keypoints, "Not all keypoints are distorted. Likely old_keypoint doesn't match any keypoint."
        
        return answers
    
    def shuffle_and_track(self, lst, fixed=False):
        first_element = lst[0]
        # Shuffle the list
        if not fixed:
            random.shuffle(lst)
        # Find the new index of the original first element
        new_index = lst.index(first_element)
        return lst, new_index

    def convert_to_MCQ_v2(self, question: Dict[str, str], num_keypoints: int = 3) -> Tuple[List, str, Dict]:
        answers = self.process_question(question, num_keypoints)
        # Don't shuffle the answers at this stage
        temp = self.prompt_results

        self.reset_prompt_results()
        return answers, 'A', temp
    
    def convert_to_MCQ(self, question: Dict[str, str], num_keypoints: int = 3) -> Tuple[str, str, Dict]:
        answers = self.process_question(question, num_keypoints)
        # Don't shuffle the answers at this stage
        new_suffle_answer_list, new_index = self.shuffle_and_track(answers, fixed=True)

        # Convert to MCQ format
        output = question['question'] + '\n'
        for i, ans in enumerate(new_suffle_answer_list):
            char = self.Index_list[i]
            output += f'{char}: {new_suffle_answer_list[i]}\n'
        temp = self.prompt_results

        self.reset_prompt_results()
        return output, self.Index_list[new_index], temp


def shuffle_and_track(lst):
    local_lst = copy.deepcopy(lst)
    first_element = local_lst[0]
    # Shuffle the list
    random.shuffle(local_lst)
    # Find the new index of the original first element
    new_index = local_lst.index(first_element)
    return local_lst, new_index

def demo():
    # Example usage
    client = openai.AzureOpenAI(api_version='2024-06-01')
    # client = openai.OpenAI()
    
    KPDistorter = KeyPointDistorter(client, seed=42)
    # Example question
    question = {
        "section_name": "self-check-questions",
        "section_text": "Question: \n2. \n\n  What are the drawbacks to analyzing the global economy on a regional basis?\n  \n Answer: 2. \n\n  A region can have some of high-income countries and some of the low-income countries. Aggregating per capita real GDP will vary widely across countries within a region, so aggregating data for a region has little meaning. For example, if you were to compare per capital real GDP for the United States, Canada, Haiti, and Honduras, it looks much different than if you looked at the same data for North America as a whole. Thus, regional comparisons are broad-based and may not adequately capture an individual country’s economic attributes.\n  \n",
        "chapter_name": "32-self-check-questions",
        "textbook_name": "principles-economics-3e",
        "chapter_url": "https://openstax.org/books/principles-economics-3e/pages/32-self-check-questions",
        "question": "\n2. \n\n  What are the drawbacks to analyzing the global economy on a regional basis?\n  \n",
        "answer": "2. \n\n  A region can have some of high-income countries and some of the low-income countries. Aggregating per capita real GDP will vary widely across countries within a region, so aggregating data for a region has little meaning. For example, if you were to compare per capital real GDP for the United States, Canada, Haiti, and Honduras, it looks much different than if you looked at the same data for North America as a whole. Thus, regional comparisons are broad-based and may not adequately capture an individual country’s economic attributes.\n  \n"
    }
    
    mcq, correct_answer = KPDistorter.convert_to_MCQ(question)
    print(mcq)
    print('correct answer:', correct_answer)

if __name__ == "__main__":
    demo()
