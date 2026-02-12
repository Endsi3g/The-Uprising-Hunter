from typing import Dict, Optional

class ObjectionHandler:
    """
    Fournit des réponses "Élite" aux objections courantes.
    """
    
    OBJECTIONS = {
        "price": {
            "trigger": ["cher", "prix", "budget", "coûteux"],
            "response": "Trop cher par rapport à quoi ? Par rapport à continuer de perdre {lost_patients} patients par mois à cause d'un site qui ne convertit pas ?"
        },
        "think": {
            "trigger": ["réfléchir", "penser", "revenir vers vous"],
            "response": "Je comprends. Souvent, 'réfléchir' veut dire qu'il reste un doute. C'est sur le prix ou sur la confiance que ça va marcher ?"
        },
        "partner": {
            "trigger": ["associé", "femme", "mari", "collègue"],
            "response": "C'est normal. Mais disons que votre associé est d'accord à 100%, est-ce que VOUS, vous êtes convaincu que c'est la solution ?"
        },
        "email": {
            "trigger": ["envoyez un mail", "documentation", "info"],
            "response": "Je peux vous envoyer de la lecture, mais mes clients réussissent parce qu'on agit, pas parce qu'on lit. On regarde ensemble si ça fit en 5 min ?"
        }
    }

    @staticmethod
    def handle_objection(text: str, context: Dict = None) -> str:
        text = text.lower()
        context = context or {"lost_patients": "10"} # Default context
        
        for key, data in ObjectionHandler.OBJECTIONS.items():
            for trigger in data["trigger"]:
                if trigger in text:
                    return data["response"].format(**context)
        
        return "Intéressant. Dites-m'en plus là-dessus ?"

class ScriptGenerator:
    """
    Génère des scripts d'intro basés sur le "Doctor Frame".
    """
    
    @staticmethod
    def generate_intro(lead_name: str, pain_point: str) -> str:
        return (
            f"Bonjour {lead_name}. Je ne vous appelle pas pour vous vendre un truc. \n"
            f"J'ai vu votre clinique et j'ai noté un problème spécifique sur {pain_point} qui doit vous coûter cher. \n"
            f"Je voulais juste vérifier si vous étiez au courant ou si c'est un choix délibéré ?"
        )

if __name__ == "__main__":
    # Test simple
    print(ObjectionHandler.handle_objection("C'est un peu cher"))
    print(ScriptGenerator.generate_intro("Dr. House", "la prise de RDV mobile"))
