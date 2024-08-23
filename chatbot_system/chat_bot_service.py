from requests import Session
from interfaces.api_interface import Chatbot
from product import product_service


class Chat_Bot_Service:

    ocassions = [
                '💼  Official',
                '🕶️  Casual',
                '🎉  Party',
            ]
    colors = [
                '⚪️ White',
                '🟢 Green',
                '🔵 Blue',
                '🌕 Yellow',
                '⚫️ Black',
            ]
    fitting = [
        'Slim',
        'Baggy',
        'Regular'
    ]
    recommendation_queries = [
        'Show more 👇',
        'Show me similar styles'
    ]
    reset_command = "Reset Recommendations 🤖"

    def chatbot(self,db:Session,chatbot_request:Chatbot):
        query = chatbot_request.query
        if query == None or query == '':
            return {
                    'type':'bot',
                    'text':'Select the perfect occasion for your outfit! 👗🎉',
                    'suggestion': self.get_suggestion('ocassion'),
                    'preference':preference
                }
        next_state = None
        current_state = self.get_current_state(query)
        preference = {
                    'color':chatbot_request.color,
                    'fitting':chatbot_request.fitting,
                    'ocassion':chatbot_request.ocassion
        }
        if current_state:
            preference[current_state] = query.split().pop().lower()
        next_state = self.get_next_state(query=query) 
        if query == self.reset_command:
            next_state = 'ocassion'
        if next_state == 'color':
            return {
                    'type':'bot',
                    'text':'Select your favorite color for your outfit! 🎨👗',
                    'suggestion': self.get_suggestion('color'),
                    'preference':preference
                }
        if next_state == 'fitting':
            return {
                    'type':'bot',
                    'text':'Pick your favorite style of clothing! 👚',
                    'suggestion': self.get_suggestion('fitting'),
                    'preference':preference
                }
        elif next_state == 'ocassion':
            return {
                    'type':'bot',
                    'text':'Select the perfect occasion for your outfit! 👗🎉',
                    'suggestion': self.get_suggestion('ocassion'),
                    'preference':preference
                }
        if query in self.colors or query in self.ocassions or query in self.fitting or query in self.recommendation_queries:
            query = f'Suggest some good shirts / t-shirts of '
            if chatbot_request.color:
                query+= f'{chatbot_request.color.split(" ").pop()} color '
            if chatbot_request.ocassion:
                query += f'for ocassion {chatbot_request.ocassion.split(" ").pop()} '
            if chatbot_request.fitting or query in self.fitting:
                query += f'and {chatbot_request.fitting.split(" ").pop()} fitting ' if query not in self.fitting else f'{query.split(" ").pop()}'

        products = product_service.Products_Service().get_recommendation(db=db,query=query)
        return {
            'type':'bot',
            'text':"Here are some top picks we've selected just for you ✨",
            'products':products,
            'questions': self.get_questions(chatbot_request=chatbot_request),
            'preference':preference

        }
    
    def get_questions(self,chatbot_request:Chatbot):
        questions = [
            self.reset_command
        ]
        if chatbot_request.color:
            questions.append(f"Show more {chatbot_request.color} shirts / T-shirts")
        if chatbot_request.ocassion:
            questions.append(f"Show more shirts / T-shirts for {chatbot_request.ocassion} ocassion")
        if chatbot_request.fitting:
            questions.append(f"Show more {chatbot_request.ocassion} fitted shirts / T-shirts")
        if chatbot_request.product.color:
            questions.append(f"Show more shirts / T-shirts similar to {chatbot_request.product.title.lower()}")
        return questions


    
    def get_next_state(self,query):
         if query in self.ocassions:
             return 'color'
         elif query in self.colors:
             return 'fitting'
         elif query in self.fitting:
             return 'carousel'
         else:
             return 'carousel'
         
    def get_current_state(self,query):
         if query in self.ocassions:
             return 'ocassion'
         elif query in self.colors:
             return 'color'
         elif query in self.fitting:
             return 'fitting'
         else:
             return None
         

    
    def get_suggestion(self,type):
        if type == 'ocassion':
            return self.ocassions
        elif type == 'color':
            return self.colors
        elif type == 'fitting':
            return self.fitting
        else:
            return []





