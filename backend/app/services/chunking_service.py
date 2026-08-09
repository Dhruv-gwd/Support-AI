def chunk_text(
    text: str, chunk_size: int = 1000, chunk_overlap: int = 150
) -> list[str]:
    """
    Split text into overlapping chunks, breaking on paragraph boundaries
    where possible so we don't cut sentences in half.

    chunk_size and chunk_overlap are in characters, not tokens — simple
    and good enough for a first pass. Swap for a token-based splitter
    later if you want tighter control over embedding costs.
    """
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            # a single paragraph longer than chunk_size gets hard-split
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - chunk_overlap):
                    chunks.append(para[i : i + chunk_size])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    # add overlap between consecutive chunks so context isn't lost at boundaries
    overlapped = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
        else:
            tail = chunks[i - 1][-chunk_overlap:]
            overlapped.append(f"{tail}\n\n{chunk}")

    return overlapped
