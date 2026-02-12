import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.payment import StripeService

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/utilities/generate_proposal.py <LeadName> <Option (1 or 2)>")
        return

    name = sys.argv[1]
    try:
        option = int(sys.argv[2])
    except ValueError:
        print("Option must be 1 or 2")
        return

    service = StripeService()
    email = service.generate_proposal_email(name, option)
    
    print("-" * 30)
    print(email)
    print("-" * 30)

if __name__ == "__main__":
    main()
