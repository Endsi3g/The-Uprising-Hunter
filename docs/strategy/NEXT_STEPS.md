# 🚀 Roadmap & Next Steps

## ✅ Completed Milestones

- [x] **Core Architecture**: Models, Enrichment, Scoring, AI Engine.
- [x] **API Integration**: Connected `Apollo.io` and `OpenAI`.
- [x] **New Source**: Integrated `Apify` for Google Maps sourcing.
- [x] **Database**: Implemented `SQLite` with `SQLAlchemy` for persistence.
- [x] **CLI**: Added command-line arguments (source, query, location).
- [x] **Automation**: Created Windows Task Scheduler script.
- [x] **Deployment**: Git initialized and codebase secured.
- [x] **Funnel "Propre"**: Implemented Step A (Scoring), Step B (Sequences), Step C (Landing/Booking), Step D (Stripe).
- [x] **Clinic Targeting**: Refined scoring engine for medical/dental leads.

## 🔜 Upcoming Priorities

### 1. Advanced Intelligence

- [ ] **Custom ICP Config**: Move scoring weights from `engine.py` to a YAML config file.
- [ ] **Intent Data**: Integrate a real intent data provider (Bombora/6sense).

### 2. Outreach & Operations

- [ ] **Email Sending**: Connect Gmail/Outlook API to send the generated sequences.
- [ ] **CRM Sync**: Push interested leads directly to HubSpot or Pipedrive.

### 3. User Interface (UI)

- [ ] **Admin Dashboard**: Build a React/Streamlit panel to manage leads and approve emails.
- [ ] **Stats**: Visualiser les taux de conversion du funnel.

## 📝 Maintenance

- Monitor API usage quotes (Apollo/OpenAI/Apify).
- Backup `prospect.db` regularly.
