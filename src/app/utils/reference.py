import uuid
import time
import random
import string


def generate_transaction_reference(prefix="TXN"):
    timestamp = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex[:8].upper()
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{timestamp}-{unique_id}-{random_suffix}"
