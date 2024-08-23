from webcolors import hex_to_rgb
import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification, GPT2Tokenizer, TFGPT2LMHeadModel, GPT2LMHeadModel, Trainer, TrainingArguments, TextDataset, DataCollatorForLanguageModeling
from datasets import Dataset
import difflib
import json
import requests
from bs4 import BeautifulSoup


class IntentGenerationService:
    def closest_color(self,r, g, b):
        color_diffs = []
        color_diffs.append((abs(r - 255) + abs(g) + abs(b), "red"))
        color_diffs.append((abs(r) + abs(g - 255) + abs(b), "green"))
        color_diffs.append((abs(r) + abs(g) + abs(b - 255), "blue"))
        return min(color_diffs, key=lambda x: x[0])[1]

    def categorize_color(self,color_name):
        rgb = hex_to_rgb(self.find_closest_match(color_name))
        return self.closest_color(rgb.red, rgb.green, rgb.blue)
    
    def find_closest_match(self,query):
        json_file = './color/colors.json'
        query = ("").join(query)
        with open(json_file, 'r') as file:
            data = json.load(file)
        if query.lower() in data:
            return '#'+data[query.lower()]
        string_list = list(data.keys())
        closest_matches = difflib.get_close_matches(query, string_list, n=1, cutoff=0.0)
        if closest_matches:
            return '#'+data[closest_matches[0]]
        else:
            return None
    
    def predict_ocassion(self,description, color):
        model_path = "./gpt2_garment_model"
        tokenizer = GPT2Tokenizer.from_pretrained(model_path)
        model = GPT2LMHeadModel.from_pretrained(model_path)
        input_text = f"Description: {description}, Color: {color} -> Occasion:"
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        output = model.generate(input_ids, max_length=50, num_return_sequences=1, temperature=0.5, pad_token_id=tokenizer.eos_token_id)
        prediction = tokenizer.decode(output[0], skip_special_tokens=True)
        return prediction.split('Occasion:')[-1].strip()



    def generate_text(self,prompt, max_length=100):
        model_name = "gpt2"
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        model = TFGPT2LMHeadModel.from_pretrained(model_name)

        encoded_input = tokenizer(prompt, return_tensors='tf')
        outputs = model.generate(
            input_ids=encoded_input['input_ids'],
            attention_mask=encoded_input['attention_mask'],
            max_length=max_length,
            num_return_sequences=1,
            do_sample= True
        )        
        # Decode the generated text to a string
        print(outputs)
        generated_text = ''
        for output in outputs:
            generated_text += tokenizer.decode(output, skip_special_tokens=True)
            print(generated_text)
        return generated_text


    def fine_tune_gpt2(self):
        # Load the dataset
        df = pd.read_csv('./intent_generation/garment_categorization.csv')

        # Prepare the text for GPT-2
        df['text'] = df.apply(lambda row: f"Description: {row['Description']}, Color: {row['Color']} -> Occasion: {row['Occasion']}", axis=1)

        # Save to a text file
        train_file = 'garment_train.txt'
        with open(train_file, 'w') as f:
            f.write('\n'.join(df['text'].tolist()))

        # Load the tokenizer and model
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        model = GPT2LMHeadModel.from_pretrained('gpt2')
        train_dataset = self.load_dataset(train_file, tokenizer)

        # Define data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer, 
            mlm=False,
        )

        # Set up training arguments
        training_args = TrainingArguments(
            output_dir="./gpt2_garment_model",
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            save_steps=10_000,
            save_total_limit=2,
            logging_dir='./logs',
            logging_steps=200,
        )

        # Initialize the Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=train_dataset,
        )

        # Train the model
        trainer.train()

        # Save the model
        trainer.save_model("./gpt2_garment_model")
        tokenizer.save_pretrained("./gpt2_garment_model")


    # Prepare the dataset for GPT-2
    def load_dataset(self,file_path, tokenizer):
        dataset = TextDataset(
            tokenizer=tokenizer,
            file_path=file_path,
            block_size=128
        )
        return dataset

    def train_bert(self):
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3)  # 3 classes: Casual, Official, Party

        # Tokenize the dataset
        def preprocess_function(examples):
            return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=128)

        # Load the dataset
        df = pd.read_csv('./intent_generation/zara_training.csv')
        df['text'] = df.apply(lambda row: f"{row['Description']} {row['Title']}", axis=1)
        df['label'] = df['Occasion'].map({'Casual': 0, 'Official': 1, 'Party': 2})  # Map to labels

        # Convert to Hugging Face dataset
        dataset = Dataset.from_pandas(df)
        tokenized_dataset = dataset.map(preprocess_function, batched=True)

        # Split into train and test
        train_test = tokenized_dataset.train_test_split(test_size=0.1)
        train_dataset = train_test['train']
        test_dataset = train_test['test']

        # Training arguments
        training_args = TrainingArguments(
            output_dir='./results',
            evaluation_strategy="epoch",
            learning_rate=2e-5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            num_train_epochs=3,
            weight_decay=0.01,
        )

        # Initialize Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
        )

        # Train the model
        trainer.train()

        # Save the model
        model.save_pretrained('./bert_garment_model')
        tokenizer.save_pretrained('./bert_garment_model')


    def predict_ocassion_bert(self,description, title):
        model = BertForSequenceClassification.from_pretrained('./bert_garment_model')
        tokenizer = BertTokenizer.from_pretrained('./bert_garment_model')
        inputs = tokenizer(f"{description} {title}", return_tensors="pt", truncation=True)
        outputs = model(**inputs)
        prediction = outputs.logits.argmax().item()
        print(prediction)
        occasions = ['Casual', 'Official', 'Party']
        return occasions[prediction]

    def calculate_bmi(self,weight, height):
        """Calculate BMI given weight in kg and height in cm."""
        if weight == 0 or height == 0:
            return 1
        return weight / ((height / 100) ** 2)

    def get_base_size(self,bmi):
        """Determine base size from BMI."""
        if bmi < 18.5:
            return "XS"
        elif 18.5 <= bmi < 22:
            return "S"
        elif 22 <= bmi < 27.5:
            return "M"
        elif 27.5 <= bmi < 32:
            return "L"
        else:
            return "XL"

    def adjust_size(self,size, adjustment):
        """Adjust size up or down."""
        sizes = ["XS", "S", "M", "L", "XL", "XXL"]
        current_index = sizes.index(size)
        new_index = max(0, min(current_index + adjustment, len(sizes) - 1))
        return sizes[new_index]

    def get_body_shape_factor(self,body_shape):
        """Return body shape factor."""
        factors = {
            "apple": 1.0,
            "pear": 0.9,
            "hourglass": 1.025,
            "rectangle": 1.06,
            "inverted triangle": 1.15
        }
        return factors.get(body_shape.lower(), 1.0)

    def recommend_size(self,height, weight, age, body_shape):
        """Recommend garment size based on given parameters."""
        if height == 0 or weight == 0 or age == 0:
            return {
                "recommended_size": 'S',
                "estimated_chest_length": 0,
                "estimated_shoulder_length": 0
            }
        height = int(height)
        weight = int(weight)
        age = int(age)
        bmi = self.calculate_bmi(weight, height)
        size = self.get_base_size(bmi)
        
        # Height adjustment
        if height > 180:
            size = self.adjust_size(size, 1)
        elif height < 160:
            size = self.adjust_size(size, -1)
        
        # Age adjustment
        if age > 50:
            size = self.adjust_size(size, 1)
        
        # Body shape adjustment
        body_shape_factor = self.get_body_shape_factor(body_shape)

        if body_shape_factor > 1:
            size = self.adjust_size(size, 1)
        
        # Estimate chest and shoulder measurements
        chest_length = (height * 0.62) * body_shape_factor
        shoulder_length = (height * 0.275) * body_shape_factor
        
        return {
            "recommended_size": size,
            "estimated_chest_length": round(chest_length, 1),
            "estimated_shoulder_length": round(shoulder_length, 1)
        }


    def get_zara_product_images_and_price(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        print(response, response.status_code)
        if response.status_code != 200:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
            return [], None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extracting images
        image_section = soup.find('ul', class_='product-detail-images__images')
        image_urls = []
        if image_section:
            sources = image_section.find_all('source')
            for source in sources:
                srcset = source.get('srcset')
                if srcset:
                    highest_res_image = srcset.split(',')[-1].split()[0]
                    image_urls.append(highest_res_image)
        
        # Extracting price
        price_tag = soup.find('span', class_='money-amount__main')
        price = None
        if price_tag:
            price_text = price_tag.text.strip()
            # Remove the currency symbol and commas, convert to a float, and then to an integer
            price = int(float(price_text.replace('₹', '').replace(',', '').strip()))

        return image_urls, price
