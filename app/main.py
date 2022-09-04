from fastapi import FastAPI


app = FastAPI()


@app.post("api/login", status_code=201)
async def login():
    return {"login": "Hello world"}


@app.post("api/register", status_code=201)
async def register():
    return {"register": "Hello world"}
