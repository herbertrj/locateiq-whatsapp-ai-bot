from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/weebook")   
async def weebook(requests:Request):
    data = await requests.json()
    print(data)
    return {"status": "Hello, World!"}