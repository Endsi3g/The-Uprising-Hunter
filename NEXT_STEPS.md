# 🚀 Roadmap & Next Steps

## ✅ Completed Milestones

- [x] **Core Architecture**: Models, Enrichment, Scoring, AI Engine.
- [x] **API Integration**: Connected `Apollo.io` and `OpenAI`.
- [x] **New Source**: Integrated `Apify` for Google Maps sourcing.
- [x] **Database**: Implemented `SQLite` with `SQLAlchemy` for persistence.
- [x] **CLI**: Added command-line arguments (source, query, location).
- [x] **Automation**: Created Windows Task Scheduler script.
- [x] **Deployment**: Git initialized and codebase secured.

## 🔜 Upcoming Priorities

### 1. Advanced Scoring & Intelligence

- [ ] **Custom ICP Config**: Move hardcoded scoring weights to a YAML config file.
- [ ] **Intent Data**: Integrate a real intent data provider (e.g., Bombora or website visitor tracking).

### 2. Outreach Automation

- [ ] **Email Sending**: Connect SMTP (Gmail/Outlook) to actually *send* the generated drafts.
- [ ] **Sequence Logic**: Implement follow-ups (Day 1, Day 3, Day 7).

### 3. User Interface (UI)

- [ ] **Dashboard**: Build a simple React/Streamlit admin panel to view leads and approve emails.
- [ ] **Stats**: Visualize conversion rates and pipeline health.

### 4. Cloud Deployment

- [ ] **Dockerize**: Create a `Dockerfile` for easy deployment.
- [ ] **Cloud Run**: Deploy the worker to a cloud provider (AWS/GCP/Render) for 24/7 operation.

## 📝 Maintenance

- Monitor API usage quotes (Apollo/OpenAI/Apify).
- Backup `prospect.db` regularly.
