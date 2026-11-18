
from quantum.bb84 import run_bb84

print("\n========== Q-SECURE BB84 SIMULATOR ==========")

# Test 1: No eavesdropper
print("\nTEST 1: Normal Communication")

result1 = run_bb84(n=1000, eve_present=False)

for key, value in result1.items():
    print(f"{key}: {value}")

# Test 2: Eve is present
print("\nTEST 2: Communication With Eve")

result2 = run_bb84(n=1000, eve_present=True)

for key, value in result2.items():
    print(f"{key}: {value}")

print("\n========== SIMULATION COMPLETED ==========")
