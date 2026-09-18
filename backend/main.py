from fastapi import FastAPI

app = FastAPI(
    title="HRN Cloud AutoVault API",
    version="1.0.0")

@app.get("/")
def root ():
    return {"message": "HRN Cloud AutoVault API is running"}

@app.get("/health")
def healthCheck():
    return {"status": "healthy"}