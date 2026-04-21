from __future__ import annotations

from dataclasses import dataclass
from typing import List, Iterator, Optional


@dataclass
class SequenceRecord:
    seq_id: str
    sequence: str
    description: str = ""


def _normalize_sequence(seq: str) -> str:
    return "".join(seq.split()).upper()


def parse_fasta_streaming(text: str, chunk_size: int = 10000) -> Iterator[SequenceRecord]:
    """
    Parse FASTA format with streaming to handle large files efficiently.
    Yields records one at a time to minimize memory usage.
    """
    current_id = ""
    current_desc = ""
    current_chunks: List[str] = []
    chunk_memory = 0
    
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith(">"):            
            if current_id:
                yield SequenceRecord(
                    seq_id=current_id,
                    description=current_desc,
                    sequence=_normalize_sequence("".join(current_chunks)),
                )
                current_chunks.clear()
                chunk_memory = 0

            header = line[1:].strip()
            if not header:
                raise ValueError("Invalid FASTA header: empty identifier.")

            parts = header.split(maxsplit=1)
            current_id = parts[0]
            current_desc = parts[1] if len(parts) > 1 else ""
        else:
            if not current_id:
                raise ValueError("Invalid FASTA format: sequence appeared before header.")
            current_chunks.append(line)
            chunk_memory += len(line)
            
            # Yield accumulated sequence if memory threshold reached
            if chunk_memory > chunk_size and current_chunks:
                combined = "".join(current_chunks)
                yield SequenceRecord(
                    seq_id=current_id,
                    description=current_desc,
                    sequence=_normalize_sequence(combined),
                )
                current_id = ""
                current_chunks.clear()
                chunk_memory = 0

    if current_id:
        yield SequenceRecord(
            seq_id=current_id,
            description=current_desc,
            sequence=_normalize_sequence("".join(current_chunks)),
        )


def parse_fasta(text: str) -> List[SequenceRecord]:
    """Parse FASTA format and return all records."""
    records = []
    for record in parse_fasta_streaming(text):
        records.append(record)
    
    if not records:
        raise ValueError("No FASTA records detected.")
    
    return records


def parse_fastq(text: str, max_records: Optional[int] = None) -> List[SequenceRecord]:
    """Parse FASTQ format with optional max records limit for large files."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) % 4 != 0:
        raise ValueError("Invalid FASTQ format: expected blocks of 4 lines.")

    records: List[SequenceRecord] = []
    record_count = 0
    
    for i in range(0, len(lines), 4):
        if max_records and record_count >= max_records:
            break
            
        header = lines[i]
        sequence = lines[i + 1]
        plus = lines[i + 2]
        quality = lines[i + 3]

        if not header.startswith("@"):
            raise ValueError("Invalid FASTQ header: expected '@'.")
        if not plus.startswith("+"):
            raise ValueError("Invalid FASTQ separator: expected '+'.")

        seq_id = header[1:].split(maxsplit=1)[0]
        if not seq_id:
            raise ValueError("Invalid FASTQ header: empty identifier.")

        norm_seq = _normalize_sequence(sequence)
        if len(norm_seq) != len(quality):
            raise ValueError("Invalid FASTQ format: sequence and quality lengths differ.")

        records.append(SequenceRecord(seq_id=seq_id, sequence=norm_seq))
        record_count += 1

    if not records:
        raise ValueError("No FASTQ records detected.")

    return records


def parse_sequences(
    text: str, 
    file_name: str = "",
    max_records: Optional[int] = None,
    max_file_size: int = 100 * 1024 * 1024  # 100MB default limit
) -> List[SequenceRecord]:
    """Parse sequences with file size limit and max records limit."""
    
    # Check file size
    if len(text) > max_file_size:
        raise ValueError(
            f"File size {len(text) / 1024 / 1024:.1f}MB exceeds "
            f"limit of {max_file_size / 1024 / 1024:.1f}MB"
        )
    
    stripped = text.lstrip()
    if not stripped:
        raise ValueError("Input is empty.")

    suffix = file_name.lower()

    if suffix.endswith((".fasta", ".fa", ".fna")) or stripped.startswith(">"):
        records = parse_fasta(text)
    elif suffix.endswith((".fastq", ".fq")) or stripped.startswith("@"):
        records = parse_fastq(text, max_records=max_records)
    else:
        # Fallback: treat as plain single-sequence text
        normalized = _normalize_sequence(stripped)
        if not normalized:
            raise ValueError("No sequence content found.")
        records = [SequenceRecord(seq_id="sequence_1", sequence=normalized)]

    # Apply max_records limit if specified
    if max_records and len(records) > max_records:
        records = records[:max_records]
    
    return records
