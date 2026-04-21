from __future__ import annotations

from typing import Dict, List, Optional

from utils.parser import SequenceRecord


VALID_BASES = set("ACGTUN")


def gc_content(sequence: str) -> float:
    """Calculate GC content efficiently using count() instead of iteration."""
    seq = sequence.upper()
    if not seq:
        return 0.0

    # Count only valid bases
    canonical_count = sum(seq.count(base) for base in VALID_BASES)
    if not canonical_count:
        return 0.0

    # Count G and C in the full sequence
    gc_count = seq.count("G") + seq.count("C")
    return round((gc_count / canonical_count) * 100, 2)


def sequence_length(sequence: str) -> int:
    return len(sequence)


def find_orfs(sequence: str, min_length: int = 90) -> List[Dict[str, int]]:
    """Find ORFs with early termination for large sequences."""
    seq = sequence.upper().replace("U", "T")
    stop_codons = {"TAA", "TAG", "TGA"}
    orfs: List[Dict[str, int]] = []
    
    # Limit ORF search for very large sequences
    max_orfs = 1000
    if len(seq) > 1_000_000:
        # For very large sequences, only search first 100KB
        seq = seq[:100_000]

    for frame in range(3):
        if len(orfs) >= max_orfs:
            break
            
        i = frame
        while i <= len(seq) - 3:
            codon = seq[i : i + 3]
            if codon == "ATG":
                j = i + 3
                while j <= len(seq) - 3:
                    stop = seq[j : j + 3]
                    if stop in stop_codons:
                        length = j + 3 - i
                        if length >= min_length:
                            orfs.append(
                                {
                                    "frame": frame,
                                    "start": i + 1,
                                    "end": j + 3,
                                    "length": length,
                                }
                            )
                        i = j
                        break
                    j += 3
            i += 3

    return orfs


def find_motif(sequence: str, motif: str) -> List[int]:
    """Find motif positions efficiently."""
    seq = sequence.upper()
    motif_upper = motif.upper()

    if not motif_upper:
        return []

    positions: List[int] = []
    start = 0
    while True:
        idx = seq.find(motif_upper, start)
        if idx == -1:
            break
        positions.append(idx + 1)
        start = idx + 1

    return positions


def summarize_sequences(
    records: List[SequenceRecord],
    compute_orfs: bool = False,
    limit_sequences: int = 10000
) -> Dict:
    """
    Summarize sequences efficiently with optional ORF computation.
    
    Args:
        records: List of sequence records
        compute_orfs: Whether to compute ORFs (expensive for large sets)
        limit_sequences: Maximum sequences to include in detail (others counted)
    """
    if not records:
        raise ValueError("No sequences available for analysis.")

    # Limit number of sequences to analyze in detail
    detail_records = records[:limit_sequences]
    remaining_count = max(0, len(records) - limit_sequences)
    
    per_sequence = []
    total_length = 0
    total_gc_bases = 0
    total_valid_bases = 0

    # Process records in detail
    for record in detail_records:
        seq = record.sequence
        length = sequence_length(seq)
        gc = gc_content(seq)

        # Count valid bases efficiently
        canonical_count = sum(seq.count(base) for base in VALID_BASES)
        total_valid_bases += canonical_count
        gc_base_count = seq.count("G") + seq.count("C")
        total_gc_bases += gc_base_count
        total_length += length

        seq_data = {
            "id": record.seq_id,
            "description": record.description,
            "length": length,
            "gc_content": gc,
        }
        
        # Only compute ORFs if requested
        if compute_orfs:
            seq_data["orf_count"] = len(find_orfs(seq))
        
        per_sequence.append(seq_data)

    # Add remaining sequences' lengths to totals (without detail)
    for record in records[limit_sequences:]:
        seq = record.sequence
        length = sequence_length(seq)
        canonical_count = sum(seq.count(base) for base in VALID_BASES)
        gc_base_count = seq.count("G") + seq.count("C")
        total_length += length
        total_valid_bases += canonical_count
        total_gc_bases += gc_base_count

    overall_gc = (
        round((total_gc_bases / total_valid_bases) * 100, 2) 
        if total_valid_bases else 0.0
    )

    result = {
        "number_of_sequences": len(records),
        "sequences_in_detail": len(detail_records),
        "total_length": total_length,
        "average_length": round(total_length / len(records), 2),
        "overall_gc_content": overall_gc,
        "sequences": per_sequence,
    }
    
    if remaining_count > 0:
        result["note"] = f"Showing details for first {limit_sequences} sequences. {remaining_count} additional sequences counted in totals."
    
    return result
