import subprocess
import sys
import os
import time

def run_command(command, cwd=None, description=None):
    """Run a command and print status."""
    if description:
        print(f"\n--- {description} ---")
    
    print(f"Executing: {' '.join(command) if isinstance(command, list) else command}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command, 
            cwd=cwd, 
            shell=True if isinstance(command, str) else False,
            check=False,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"PASS ({duration:.2f}s)")
            return True, result.stdout
        else:
            print(f"FAIL ({duration:.2f}s)")
            print("Error Output:")
            print(result.stderr)
            print("Standard Output:")
            print(result.stdout)
            return False, result.stderr
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False, str(e)

def main():
    print("==================================================")
    print("      PROSPECT SYSTEM - FULL VERIFICATION")
    print("==================================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    verification_dir = os.path.join(base_dir, "scripts", "verification")
    ops_dir = os.path.join(base_dir, "scripts", "ops")
    admin_dir = os.path.join(base_dir, "admin-dashboard")
    
    results = {}
    
    # 1. Verify Core System & Advanced Features
    success, _ = run_command(
        [sys.executable, os.path.join(verification_dir, "verify_advanced_system.py")], 
        cwd=base_dir,
        description="Verifying Core Sales Logic & Scoring"
    )
    results["Core Logic"] = success
    
    # 2. Verify Follow-up Logic
    success, _ = run_command(
        [sys.executable, os.path.join(verification_dir, "test_followup_logic.py")],
        cwd=base_dir,
        description="Verifying Follow-up Engine State Machine"
    )
    results["Follow-up Logic"] = success

    # 3. Verify Elite Tactics (Sales Scripting)
    success, _ = run_command(
        [sys.executable, "-c", "from src.sales.elite_tactics import ObjectionHandler; print(ObjectionHandler.handle_objection('C\\'est trop cher'))"],
        cwd=base_dir,
        description="Verifying Elite Sales Tactics"
    )
    results["Elite Sales Tactics"] = success

    # 4. Verify Backend API import (Admin API)
    print("\n--- Verifying Backend API Import ---")
    success, _ = run_command(
        [sys.executable, "-c", "from src.admin.app import app; print('Admin API import successful')"],
        cwd=base_dir,
        description="Verifying Backend API Import"
    )
    results["Backend API"] = success

    # 5. Verify basic healthcheck script
    success, _ = run_command(
        [sys.executable, os.path.join(ops_dir, "healthcheck.py"), "--skip-http"],
        cwd=base_dir,
        description="Running local healthcheck (DB + scoring config)"
    )
    results["Healthcheck"] = success

    # 5. Verify Admin Dashboard Build (Frontend)
    if os.path.exists(admin_dir):
        # Check if node_modules exists, if not install
        if not os.path.exists(os.path.join(admin_dir, "node_modules")):
             success, _ = run_command(
                "npm install",
                cwd=admin_dir,
                description="Installing Frontend Dependencies"
            )
             if not success:
                 results["Frontend Install"] = False
        
        success, _ = run_command(
            "npm run build",
            cwd=admin_dir,
            description="Verifying Frontend Build (Next.js)"
        )
        results["Frontend Build"] = success
    else:
        print("\nAdmin directory not found.")
        results["Frontend Build"] = False

    # Summary
    print("\n==================================================")
    print("               VERIFICATION SUMMARY")
    print("==================================================")
    all_passed = True
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{test:<25} : {status}")
        if not passed:
            all_passed = False
            
    print("==================================================")
    
    if all_passed:
        print("\nALL SYSTEMS OPERATIONAL. READY FOR LOCAL DEPLOYMENT.")
        print("\nTo start the local dashboard:")
        print(f"cd admin-dashboard && npm run dev")
    else:
        print("\nSOME SYSTEMS FAILED. REVIEW LOGS ABOVE.")
        sys.exit(1)

if __name__ == "__main__":
    main()
