from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.wsgi import WSGIMiddleware
from pymongo import MongoClient
from pydantic import EmailStr
import bcrypt
import uvicorn
from flask import Flask, render_template

# Init Flask api
flask_app = Flask(__name__)

# Init FastAPI
app = FastAPI()

# MongoDB setup
client = MongoClient('localhost', 27017)
db = client['remotebricks_db']

# mount flask on fastapi
app.mount("/aa", WSGIMiddleware(flask_app))

# Flask section
@flask_app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html', content="Hello World")

@flask_app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html', content="Hello World")

@flask_app.route('/link', methods=['GET'])
def link_page():
    return render_template('link.html', content="Hello World")

@flask_app.route('/delete', methods=['GET'])
def delete_page():
    return render_template('delete.html', content="Hello World")


# helper function - to hash passwords
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# helper function - to verify passwords
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# FastAPI section

# root page
@app.get("/")
async def root_page():
    return {'text':'hehe'}

# registration api
# http://127.0.0.1:8000/aa/register
@app.post("/register")
async def register_user(username: str = Form(...), email: EmailStr = Form(...), password: str = Form(...)):
    # check if username already exists
    if db.user.find_one({'username': username}):
        raise HTTPException(status_code=400,detail="username already exists. try again.")
    hashpass = hash_password(password)
    user_data = {
        "username":username,
        "email": email,
        "password": hashpass
    }
    result = db.user.insert_one(user_data)          # inserting in 'user' collection in db
    return {"message":"User registered successfully", "user_id": str(result.inserted_id)}

# login api
# http://127.0.0.1:8000/aa/login
@app.post("/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    result = db.user.find_one({'username': username})
    if not result or not verify_password(password, result['password']):
        raise HTTPException(status_code=404, detail="user not found")
    return {"message": "Welcome aboard", "user_id": str(result['_id'])}

# linkid api
# http://127.0.0.1:8000/aa/link
@app.post("/link")
async def link_id(username: str = Form(...), link_id: str = Form(...)):
    # for joining - referencing document method is used. (we can use aggregation method to merge queries)

    result = db.user.find_one({'username': username})
    if not result:
        raise HTTPException(status_code=404, detail="user not found")
    user = {
        "user_id": result['_id'],
        "link_id": link_id
    }
    insert_result = db.link.insert_one(user)
    return {"message": "user link successful", "id": str(insert_result.inserted_id)}

# delete api
# http://127.0.0.1:8000/aa/delete
@app.post("/delete")
async def delete_user(username: str = Form(...)):
    result = db.user.find_one({'username': username})
    if not result:
        raise HTTPException(status_code=404, detail="user not found")
    
    # for chain delete 
    # repeat the following line for each collection
    # db.OtherCollection.delete_many({'_id':result['_id']})
    db.user.delete_one({'_id': result['_id']})
    db.link.delete_many({'user_id': result['_id']})
    
    return {"message": "deleted", "user_id": str(result['_id'])}
        



if __name__=="__main__":
    uvicorn.run(app,host='127.0.0.1',port=8000)
    