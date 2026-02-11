from src.enrichment.client import MockApolloClient, ApolloClient
from src.enrichment.apify_client import ApifyMapsClient
from src.workflows.manager import WorkflowManager
from src.core.database import engine, Base, SessionLocal
from src.core.db_models import DBLead, DBCompany, DBInteraction
from src.core.models import Lead
import os
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_db():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)

def save_lead_to_db(lead: Lead, session):
    # check if company exists
    db_company = session.query(DBCompany).filter(DBCompany.domain == lead.company.domain).first()
    if not db_company:
        db_company = DBCompany(
            name=lead.company.name,
            domain=lead.company.domain,
            industry=lead.company.industry,
            size_range=lead.company.size_range,
            revenue_range=lead.company.revenue_range,
            tech_stack=lead.company.tech_stack,
            description=lead.company.description,
            linkedin_url=str(lead.company.linkedin_url) if lead.company.linkedin_url else None,
            location=lead.company.location
        )
        session.add(db_company)
        session.flush() # get ID

    # check if lead exists
    db_lead = session.query(DBLead).filter(DBLead.email == lead.email).first()
    if not db_lead:
        db_lead = DBLead(
            id=lead.email, # Using email as ID
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            title=lead.title,
            phone=lead.phone,
            linkedin_url=str(lead.linkedin_url) if lead.linkedin_url else None,
            company_id=db_company.id,
            status=lead.status,
            demographic_score=lead.score.demographic_score,
            behavioral_score=lead.score.behavioral_score,
            intent_score=lead.score.intent_score,
            total_score=lead.score.total_score,
            score_breakdown=lead.score.score_breakdown,
            interactions=[] 
        )
        session.add(db_lead)
    
    session.commit()

def main():
    parser = argparse.ArgumentParser(description="Automated Prospecting System")
    parser.add_argument("--source", choices=["apollo", "apify", "mock"], default="mock", help="Data source to use")
    parser.add_argument("--industry", help="Target industry")
    parser.add_argument("--role", help="Target role (e.g. 'CTO')")
    parser.add_argument("--location", help="Target location")
    parser.add_argument("--query", help="Generic search query (for Apify mainly)")
    parser.add_argument("--limit", type=int, default=10, help="Max results to fetch")
    
    args = parser.parse_args()

    print("==================================================")
    print("   AUTOMATED PROSPECTING SYSTEM - PRODUCTION RUN")
    print("==================================================\n")
    
    # Initialize Database
    init_db()
    db_session = SessionLocal()

    # Initialize System with appropriate client
    client = None
    
    if args.source == "apollo":
        apollo_key = os.getenv("APOLLO_API_KEY")
        if apollo_key and apollo_key != "your_apollo_api_key_here":
            print("✅ Using REAL Apollo Client")
            client = ApolloClient(api_key=apollo_key)
        else:
            print("❌ invalid APOLLO_API_KEY. Falling back to Mock.")
            client = MockApolloClient()
            
    elif args.source == "apify":
        apify_token = os.getenv("APIFY_API_TOKEN")
        if apify_token and apify_token != "your_apify_api_token_here":
            print("✅ Using Apify Client (maps scraper)")
            client = ApifyMapsClient(api_token=apify_token)
        else:
             print("❌ invalid APIFY_API_TOKEN. Falling back to Mock.")
             client = MockApolloClient()
             
    else: # Mock
        print("⚠️  Using MOCK Apollo Client (Default)")
        client = MockApolloClient()
        
    workflow = WorkflowManager(client)
    
    # Define Target Criteria from Args
    target_criteria = {}
    if args.industry: target_criteria["industry"] = args.industry
    if args.role: target_criteria["role"] = args.role
    if args.location: target_criteria["location"] = args.location
    if args.query: target_criteria["query"] = args.query
    target_criteria["limit"] = args.limit
    
    # Default fallback for demo if no args provided and using mock
    if args.source == "mock" and not target_criteria:
         target_criteria = {
            "industry": "Software",
            "role": "CTO",
            "location": "US",
            "company_domains": ["techcorp.com", "healthplus.com"]
        }
    
    # Run Workflow
    print(f"Running workflow with criteria: {target_criteria}")
    results = workflow.process_lead_criteria(target_criteria)
    
    print("\n==================================================")
    print("   FINAL REPORT")
    print("==================================================")
    
    saved_count = 0
    for lead in results:
        print(f"\nLead: {lead.first_name} {lead.last_name} | Company: {lead.company.name}")
        print(f"Status: {lead.status}")
        print(f"Score: {lead.score.total_score:.2f}")
        
        # Persist to DB
        # Only save if we have an email (ID)
        if lead.email:
            try:
                save_lead_to_db(lead, db_session)
                saved_count += 1
            except Exception as e:
                print(f"Error saving lead {lead.email}: {e}")
        else:
            print("⚠️  Skipping DB save: No email provided.")
        
    print(f"\nSaved {saved_count} leads to database.")
    db_session.close()

if __name__ == "__main__":
    main()
