from typing import List
from ..core.models import Lead

class AuditHelper:
    """
    Generates talking points for a Loom audit based on lead scoring data.
    """
    
    @staticmethod
    def generate_talking_points(lead: Lead) -> str:
        points = []
        score = lead.score
        
        # Introduction
        points.append(f"👋 Intro: Bonjour {lead.first_name}, vu votre clinique {lead.company.name}...")
        
        # Pain Points Analysis (based on ICP breakdown)
        icp = score.icp_breakdown
        
        if icp.get('pain_high_friction', 0) > 0:
            points.append("⚠️ PAIN: Mentionnez la friction de prise de RDV (trop de clics).")
        if icp.get('digital_weakness_mobile', 0) > 0:
            points.append("📱 MOBILE: Montrez que le site est cassé sur mobile / CTA invisible.")
        if icp.get('pain_no_faq', 0) > 0:
            points.append("❓ FAQ: Soulignez l'absence de réponses aux objections (prix, douleur).")
            
        # Solution Tease
        points.append("🚀 SOL: Imaginez un agenda qui se remplit seul, sans téléphone.")
        
        # CTA
        points.append("📞 CTA: 2 options en bas de l'email. Appel 15 min ?")
        
        return "\n".join(points)
