import pandas as pd
import numpy as np

# Create a dataset with intentional production anomalies
data = {
    "order_id": [1001, 1002, 1003, 1004, 1005, 1005, 1007], # Note duplicate 1005
    "customer_id": ["C101", "C102", None, "C104", "C105", "C106", "C107"], # Null value
    "amount": [150.50, -20.00, 89.99, 1200.00, 45.00, 0.00, 310.25], # Negative value
    "status": ["DELIVERED", "SHIPPED", "PENDING", "UNKNOWN_STATUS", "DELIVERED", "CANCELLED", "PENDING"],
    "email": ["alice@work.com", "bob_at_email.com", "charlie@test.com", "dana@domain.co", "eva@mail.com", "frank@corp.com", "grace@tech.io"]
}

df = pd.DataFrame(data)
df.to_csv("production_orders.csv", index=False)
print("Created production_orders.csv with 7 records and deliberate anomalies.")