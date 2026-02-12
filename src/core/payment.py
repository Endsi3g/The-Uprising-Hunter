import stripe
import os
from typing import Optional

class StripeService:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_API_KEY")
        if self.api_key:
            stripe.api_key = self.api_key
        
        # Default price IDs for the two options mentioned in the logic
        self.option_1_price_id = os.getenv("STRIPE_PRICE_ID_OPTION_1")
        self.option_2_price_id = os.getenv("STRIPE_PRICE_ID_OPTION_2")

    def create_payment_link(self, option: int = 1) -> Optional[str]:
        """
        Generates a Stripe Payment Link for live closing.
        """
        if not self.api_key:
            if os.getenv("DEMO_MODE") == "true":
                return "https://checkout.stripe.com/mock_link" # Placeholder for demo
            raise ValueError("STRIPE_API_KEY is not configured in environment variables.")
            
        price_id = self.option_1_price_id if option == 1 else self.option_2_price_id
        
        if not price_id:
            return None
            
        try:
            payment_link = stripe.PaymentLink.create(
                line_items=[{"price": price_id, "quantity": 1}],
                after_completion={
                    "type": "redirect", 
                    "redirect": {"url": os.getenv("SUCCESS_REDIRECT_URL", "https://votre-site.fr/success")}
                }
            )
            return payment_link.url
        except Exception as e:
            print(f"Stripe Error: {e}")
            return None

    def get_live_close_options(self):
        """
        Returns the two options to show during the sales call.
        """
        return {
            "Option 1": "Installation & Setup Rapide (One-time)",
            "Option 2": "Accompagnement Premium & Automatisation Complète (Mensuel)"
        }

    def generate_proposal_email(self, lead_name: str, option_selected: int) -> str:
        """
        Generates the post-call recap email with the payment link.
        """
        link = self.create_payment_link(option_selected)
        
        if option_selected not in (1, 2):
            raise ValueError("Invalid option selected. Must be 1 or 2.")

        if option_selected == 1:
            offer_name = "Système d'Acquisition Rapide (Setup)"
            price = "500$ (Une fois)"
            bullets = [
                "✅ Audit complet & Fixes immédiats",
                "✅ Mise en place du système de RDV",
                "✅ Optimisation Page Google My Business"
            ]
        else:
            offer_name = "Partenariat Croissance & Automatisation"
            price = "150$/mois"
            bullets = [
                "✅ Tout le pack Setup inclus",
                "✅ Campagnes de réactivation mensuelles",
                "✅ Support & Mises à jour illimitées"
            ]
            
        bullet_text = "\n".join(bullets)
        
        email_content = f"""
        Objet : Récapitulatif & Lancement - {offer_name}
        
        Bonjour {lead_name},
        
        Comme discuté, voici le plan pour transformer votre acquisition patient dès cette semaine.
        
        **Votre Offre : {offer_name}**
        Prix : {price}
        
        Ce que nous allons faire :
        {bullet_text}
        
        **Lien de paiement sécurisé pour démarrer :**
        👉 [Cliquez ici pour valider]({link})
        
        Dès réception, je commence l'audit approfondi et vous recevez le premier rapport sous 48h.
        
        À très vite,
        """
        return email_content
