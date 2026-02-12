# 🧠 Système de Scoring Intelligent & Flow de Vente

Ce document définit l'architecture du système de scoring intelligent et le flow complet de transformation des leads froids en clients payants.

## 1. Le Principe : Dual Scoring (Fit vs. Intent)

On ne suit pas un seul score, mais deux dimensions distinctes :

- **Score ICP (0–100)** : "Est-ce que c’est le bon type de clinique ?" (Priorisation).
- **Heat Score (0–100)** : "Est-ce que ce lead est chaud maintenant ?" (Timing & Actions).

---

## 2. Score ICP (0–100) — Modèle Hybride

*Sert à définir si le prospect mérite un effort personnalisé (ex: Loom).*

### 2.1 Fit (0–30)

- **Taille (2–5 praticiens)** : +15
- **Clinique standard** (GMF, Dentaire, Physio) : +10
- **Zone géographique prioritaire** : +5
- **Présence d'un gestionnaire/admin** : +2
- *Pénalité Cabinet solo* : -6
- *Pénalité Très gros groupe (10+)* : -4 (cycle de décision trop long)

### 2.2 Pain (0–35)

- **Prise de RDV floue / multiple** : +12
- **Absence de section "Nouveaux Patients / FAQ"** : +8
- **Infos essentielles manquantes** (horaires, langues) : +6
- **Friction excessive** (Formulaires longs, "appelez-nous" unique) : +6
- **Signes de surcharge** ("achalandé", "sans RDV") : +3

### 2.3 Digital Weakness (0–20)

- **Mobile mauvais** (CTA non cliquables, texte minuscule) : +10
- **CTA non visible above the fold** : +6
- **Page Contact faible** (pas de map, pas d'instructions) : +4

### 2.4 Access & Urgency (0–15)

- **Email direct présent** : +6
- **Post/Actu récente** : +2
- **Recrutement actif** : +2
- **Nouveau service annoncé** : +1

---

## 3. Heat Score (0–100) — Le Score "Chaud"

*Sert à déclencher le closing ou les relances agressives.*

### 3.1 Engagement Email (0–40)

- **Ouverture** : +5
- **Clic (Calendly/Loom/Landing)** : +15
- **2+ ouvertures** : +10
- **Forward détecté** : +10

### 3.2 Engagement Site/Reply (0–50)

- **Visite page prix/offre** : +10
- **Retour sur le site < 48h** : +7
- **Réponse positive ("Ok pour audit/détails")** : +15
- **Réponse "Pas maintenant"** : +8 (Mise en nurture)

### 3.3 Timing (0–10)

- **Action dans les < 24h** : +10
- **Action dans les < 48h** : +6

---

## 4. Niveaux & Actions Automatiques (La Machine)

| ICP Score | Tier | Action Outreach |
| :--- | :--- | :--- |
| **80–100** | **Tier A** | Loom personnalisé + Proposition RDV 15 min + Follow-up J+2/5/9 |
| **60–79** | **Tier B** | Email personnalisé + Offre audit (Loom si Heat > 40) |
| **40–59** | **Tier C** | DM / Porte-à-porte / Nurture contenu |
| **< 40** | **Tier D** | Skip / Archivage |

| Heat Score | Statut | Action Automatique |
| :--- | :--- | :--- |
| **≥ 70** | **Hot** | Proposer RDV immédiat + Envoi direct lien Stripe possible |
| **40–69** | **Warm** | Envoyer Audit Loom + Proposer 2 créneaux |
| **< 40** | **Cold** | Continuer séquence de valeur |

---

## 5. Flow Complet : Froid → Chaud → Payé

1. **Ingestion** (Google Maps) : Scraping & Normalisation.
2. **Scoring & Seg** : Calcul ICP & Attribution Tier.
3. **Outreach** : Séquence J+1 (Focus 15 min call).
4. **Warm-up** : Envoi Loom si Tier A ou Heat > 40.
5. **Closing Call** : Diagnostic 15 min + 2 options d'offre + **Stripe Link Live**.
6. **Sprint 7 Jours** : Livraison standardisée (Structure, Build, Mobile, Trust).
7. **Feedback Loop** : Témoignage + Referral + Upsell mensuel.

---

## 7. Fit & Scoring Edge Cases

### 7.1 Fit Penalties (The "Avoid" List)

Certain attributes trigger automatic penalties to prevent the AI from wasting energy on low-value prospects:

- **Solo Cabinets (-6)**: Generally too small for complex AI automation ROI.
- **Micro-Industry Mismatch**: While we target health, general business services detected on medical sites (e.g. coffee shop inside) are deprioritized.
- **Large Groups (10+) (-4)**: High value but extremely long sales cycles; excluded from fast-track Tier A Loom sequences.

### 7.2 Overlapping Ranges Awareness

Size ranges from external sources (Apollo/LinkedIn) are normalized as follows:

- **1-4 / 1-10**: Mapped to "Small" (High Fit if >1).
- **11-50**: Mapped to "Medium" (Tier B focus).
- Overlapping strings (like "2-10" vs "10+") are resolved by favoring the more specific numeric range if available in `lead.details`.

### 7.3 Google Maps & Data Compliance

We adhere to Google Maps Platform Terms of Service regarding data scraping:

- **No Permanent Caching**: We only store public business identifiers.
- **Redaction**: Personal emails (GMail/Outlook) found on public sites are redacted or flagged for manual review to ensure PII compliance.
- **Attribution**: All derived scores cite the original source timestamp.

---

## 8. ICP vs. Heat Interaction

The system uses a 2D matrix to decide focus:

- **High ICP / Low Heat**: Nurture via high-value content (Loom).
- **Low ICP / High Heat**: Short-circuit to automated self-serve devis.
- **High ICP / High Heat**: **CRITICAL PRIORITY**. Manual salesperson takeover.
