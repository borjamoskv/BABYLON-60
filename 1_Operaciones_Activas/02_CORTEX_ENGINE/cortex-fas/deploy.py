# deploy.py
import subprocess
import os
import sys

def check_env():
    required = ["STRIPE_KEY", "STRIPE_PRICE_STARTER", "DATABASE_URL", "API_KEY_SECRET"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"❌ Missing env vars: {missing}")
        sys.exit(1)
    print("✅ Env vars OK")

def build():
    print("🔨 Building...")
    subprocess.run(["docker-compose", "-f", "docker-compose.prod.yml", "build"], check=True)
    print("✅ Build OK")

def migrate():
    print("🗄️  Running migrations...")
    subprocess.run([
        "docker-compose", "-f", "docker-compose.prod.yml",
        "run", "--rm", "api",
        "psql", os.getenv("DATABASE_URL"), "-f", "db/migrations.sql"
    ], check=True)
    print("✅ Migrations OK")

def deploy():
    print("🚀 Deploying...")
    subprocess.run(["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"], check=True)
    print("✅ Deploy OK")

def health_check():
    import urllib.request
    url = "http://localhost:8000/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            print(f"✅ Health check OK: {r.read().decode()}")
    except Exception as e:
        print(f"❌ Health check FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_env()
    build()
    migrate()
    deploy()
    health_check()
