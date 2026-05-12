import tiktoken

# Use cl100k_base encoding for all models (close enough for budgeting)
_enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(_enc.encode(text))

class ContextBudget:
    def __init__(self, total: int):
        self.total = total
        self.used = 0

    def fits(self, text: str) -> bool:
        return self.used + count_tokens(text) <= self.total

    def consume(self, text: str) -> None:
        self.used += count_tokens(text)

    def remaining(self) -> int:
        return self.total - self.used

    def utilization(self) -> float:
        return self.used / self.total
