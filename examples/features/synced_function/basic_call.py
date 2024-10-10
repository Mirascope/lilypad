import lilypad


@lilypad.llm_fn(synced=True)
def recommend_book(genre: str) -> str: ...
