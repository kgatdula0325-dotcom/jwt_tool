import os
import json

print("Script started")

TABBY_CARD_LIMIT_URL = "https://api.tabby.ai/api/v2/customer/card/limit"
DEFAULT_TIMEOUT = 30

customer_id = os.getenv("0709aef6-307e-4303-95ea-eaee09594559")
bearer_token = os.getenv("eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzY2MjA2NDYsImlhdCI6MTc3NjYxOTQ0NiwiaXNzIjoidGFiYnkuYWkiLCJjdXN0b21lcl9pZCI6IjA3MDlhZWY2LTMwN2UtNDMwMy05NWVhLWVhZWUwOTU5NDU1OSIsInNlc3Npb25faWQiOiIzZmRmZTlkNC1jYTE0LTRjMGYtYTlhNC0zMzhiYTdjMGM0NDgiLCJtZXRhZGF0YSI6eyJ0cnVzdGVkX2RldmljZV9pbnN0YWxsYXRpb25faWQiOiIyNTVCNEUyRC0xODJFLTRBOTUtOTk4Qy03NENEQkI5QTkzODAiLCJ0cnVzdGVkX2RldmljZV9pc190cnVzdGVkIjp0cnVlfX0.zgTJdM5-ieofDDH-lFFYJwHL41RnXQmcQIA4TjzFNxU2tn10BXplHcMvgM5c0B4XJzlq-M22Czb3CKi51UV2Sg")
reason = os.getenv("TABBY_REASON", "limit_update")
new_limit = float(os.getenv("TABBY_LIMIT", "15000"))

request_preview = {
    "url": TABBY_CARD_LIMIT_URL,
    "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzY2MjA2NDYsImlhdCI6MTc3NjYxOTQ0NiwiaXNzIjoidGFiYnkuYWkiLCJjdXN0b21lcl9pZCI6IjA3MDlhZWY2LTMwN2UtNDMwMy05NWVhLWVhZWUwOTU5NDU1OSIsInNlc3Npb25faWQiOiIzZmRmZTlkNC1jYTE0LTRjMGYtYTlhNC0zMzhiYTdjMGM0NDgiLCJtZXRhZGF0YSI6eyJ0cnVzdGVkX2RldmljZV9pbnN0YWxsYXRpb25faWQiOiIyNTVCNEUyRC0xODJFLTRBOTUtOTk4Qy03NENEQkI5QTkzODAiLCJ0cnVzdGVkX2RldmljZV9pc190cnVzdGVkIjp0cnVlfX0.zgTJdM5-ieofDDH-lFFYJwHL41RnXQmcQIA4TjzFNxU2tn10BXplHcMvgM5c0B4XJzlq-M22Czb3CKi51UV2Sg" if bearer_token else "Bearer MISSING",
        "Content-Type": "application/json",
    },
    "json": {
        "customer_id": customer_id,
        "new_limit": new_limit,
        "reason": reason,
    },
    "timeout": DEFAULT_TIMEOUT,
}

print(json.dumps(request_preview, indent=2))