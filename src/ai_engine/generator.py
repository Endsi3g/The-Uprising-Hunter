from .prompts import COLD_EMAIL_TEMPLATE, LINKEDIN_CONNECTION_TEMPLATE, LINKEDIN_MESSAGE_TEMPLATE
from ..core.models import Lead
from openai import OpenAI
import os

class MessageGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def generate_gpt_content(self, prompt: str) -> str:
        if not self.client:
            return None
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # or gpt-4o
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Generation Error: {e}")
            return None

    def generate_cold_email(self, lead: Lead) -> str:
        # Determine pain point area based on title/industry (simple logic for now)
        pain_point_area = "developer productivity"
        pain_point = "managing technical debt"
        if "sales" in (lead.title or "").lower():
             pain_point_area = "pipeline velocity"
             pain_point = "lead qualification time"

        # Try AI generation first
        if self.client:
            prompt = f"""
            Write a personalized cold email to {lead.first_name} {lead.last_name}, {lead.title} at {lead.company.name}.
            
            Context:
            - Company Industry: {lead.company.industry}
            - Company Description: {lead.company.description}
            - Pain Point: {pain_point}
            - Value Prop: Automating manual prospecting work
            
            Keep it under 150 words, professional but conversational.
            """
            content = self.generate_gpt_content(prompt)
            if content:
                return content

        # Fallback to template
        content = COLD_EMAIL_TEMPLATE.format(
            first_name=lead.first_name,
            company_name=lead.company.name,
            pain_point_area=pain_point_area,
            company_focus=lead.company.description or "growth",
            job_title=lead.title or "leader",
            pain_point=pain_point,
            related_competitor="Industry Leaders",
            value_proposition="automating the busywork"
        )
        return content

    def generate_linkedin_connect(self, lead: Lead) -> str:
        # Try AI generation first
        if self.client:
            prompt = f"""
            Write a LinkedIn connection request message (max 300 chars) for {lead.first_name} {lead.last_name}, {lead.title} at {lead.company.name}.
            Mention shared interest in {lead.company.industry or 'tech'}.
            """
            content = self.generate_gpt_content(prompt)
            if content:
                return content

        content = LINKEDIN_CONNECTION_TEMPLATE.format(
            first_name=lead.first_name,
            company_name=lead.company.name,
            industry=lead.company.industry or "Tech",
            job_title=lead.title or "Leader"
        )
        return content
