
import numpy as np


def generate_random_bits(n):
    """Generate Alice's random binary bits."""
    return np.random.randint(0, 2, n)


def generate_random_bases(n):
    """0 = Rectilinear (Z), 1 = Diagonal (X)."""
    return np.random.randint(0, 2, n)


def measure_qubit(alice_bit, alice_basis, measurement_basis):
    """
    Simulate measurement of a BB84 qubit.

    Same basis: obtain the original bit.
    Different basis: obtain a random bit.
    """
    if alice_basis == measurement_basis:
        return alice_bit

    return np.random.randint(0, 2)


def run_bb84(n=100, eve_present=False):
    """Execute the BB84 quantum key distribution protocol."""

    # Step 1: Alice generates bits and bases
    alice_bits = generate_random_bits(n)
    alice_bases = generate_random_bases(n)

    # Step 2: Eve intercepts the qubits (if enabled)
    received_bits = []

    for i in range(n):
        if eve_present:
            eve_basis = np.random.randint(0, 2)

            eve_bit = measure_qubit(
                alice_bits[i],
                alice_bases[i],
                eve_basis
            )

            # Eve resends the state she measured
            received_bits.append((eve_bit, eve_basis))

        else:
            received_bits.append(
                (alice_bits[i], alice_bases[i])
            )

    # Step 3: Bob generates random measurement bases
    bob_bases = generate_random_bases(n)
    bob_bits = []

    for i in range(n):
        received_bit, received_basis = received_bits[i]

        bob_bit = measure_qubit(
            received_bit,
            received_basis,
            bob_bases[i]
        )

        bob_bits.append(bob_bit)

    bob_bits = np.array(bob_bits)

    # Step 4: Alice and Bob compare their bases
    matching_indices = np.where(
        alice_bases == bob_bases
    )[0]

    alice_sifted = alice_bits[matching_indices]
    bob_sifted = bob_bits[matching_indices]

    # Step 5: Reveal a random sample for error checking
    total_sifted = len(matching_indices)

    if total_sifted == 0:
        return {
            "error": "No matching bases. Run the protocol again."
        }

    sample_size = max(1, int(total_sifted * 0.25))

    sample_indices = np.random.permutation(
        total_sifted
    )[:sample_size]

    sample_errors = np.sum(
        alice_sifted[sample_indices] !=
        bob_sifted[sample_indices]
    )

    qber = (sample_errors / sample_size) * 100

    # Remaining bits form the demonstration shared key
    remaining_indices = np.setdiff1d(
        np.arange(total_sifted),
        sample_indices
    )

    shared_key = ''.join(
        map(str, alice_sifted[remaining_indices])
    )

    # Step 6: Decide whether to accept the key
    security_status = (
        "SECURE" if qber <= 11 else "EAVESDROPPING DETECTED"
    )

    if security_status != "SECURE":
        shared_key = ""

    return {
        "total_qubits": n,
        "matching_bases": total_sifted,
        "sample_size": sample_size,
        "sample_errors": int(sample_errors),
        "qber": round(float(qber), 2),
        "security_status": security_status,
        "shared_key": shared_key,
        "key_length": len(shared_key),
        "eve_present": eve_present
    }
