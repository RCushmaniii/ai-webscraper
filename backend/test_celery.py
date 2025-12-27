import os
import ssl
from celery import Celery

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL")
backend_url = os.getenv("CELERY_RESULT_BACKEND")

print(f"Broker URL: {broker_url}")
print(f"Backend URL: {backend_url}")

# Configure SSL
broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
}

# Create Celery app
app = Celery(
    "test",
    broker=broker_url,
    backend=backend_url
)

# Configure SSL
app.conf.update(
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=broker_use_ssl
)

print("Celery app created successfully!")
print(f"Broker: {app.conf.broker_url}")
print(f"Backend: {app.conf.result_backend}")

# Test sending a simple task
@app.task
def test_task():
    return "Hello from Celery!"

try:
    result = test_task.delay()
    print(f"Task sent successfully! Task ID: {result.id}")
except Exception as e:
    print(f"Error sending task: {e}")
    import traceback
    traceback.print_exc()
