from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session, aliased
from random import randint
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost.donation.com",
    "https://localhost.organdonation.com",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class Users(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=100)
    mobile: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)
    isAdmin: bool = Field(default=False)
    address: str = Field(min_length=1, max_length=100)
    bloodGroup: str = Field(min_length=1, max_length=3)
    hospital_id: int = Field()
    isAlive: bool = Field(default=False)
    isDonor: bool = Field(default=False)
    isRecipient: bool = Field(default=False)

class Organs(BaseModel):
    organ_name: str = Field(min_length=1, max_length=100)

class Hospital(BaseModel):
    hospital_name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=100)

class Donations(BaseModel):
    donor_id: int = Field()
    recipient_id: int = Field()
    organ_id: int = Field()
    status: str = Field(min_length=1, max_length=100)

@app.get("/")
async def root(db:Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.isAdmin == True).first()
    if user_model is None:
        user_model = models.Users()
        user_model.first_name = "admin"
        user_model.last_name = ""
        user_model.email = "admin@gmail.com"
        user_model.mobile = ""
        user_model.password = "root"
        user_model.isAdmin = True
        db.add(user_model)
        db.commit()
    organCount = db.query(models.Organs).count()
    if organCount == 0:
        organs_data = [
            "Kidney",
            "Liver",
            "Eye",
            "Heart",
            "Lungs",
            "Pancreas",
            "Intestines"
        ]
        for data in organs_data:
            organ_model = models.Organs()
            organ_model.organ_name = data
            db.add(organ_model)
        db.commit()
    hospitalCount = db.query(models.Hospital).count()
    if hospitalCount == 0:
        hospitals_data = [
            "Apollo Hospital",
            "Medanta",
            "Fortis Hospital",
            "BLK Hospital",
            "AIIMS",
            "Max Super Speciality Hospital"
        ]
        for data in hospitals_data:
            hospital_model = models.Hospital()
            hospital_model.hospital_name = data
            db.add(hospital_model)
        db.commit()
    return {"message": "Hello World"}

@app.get("/getAllUsers")
async def read(db:Session = Depends(get_db)):
    return db.query(models.Users).all()

@app.get("/getUsersByTokenId")
async def read(user_id:int, db:Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        return user
        
@app.post("/registerUser")
async def create(user: Users, db:Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.email == user.email).first()
    if user_model is None:
        user_model = models.Users()
        user_model.first_name = user.first_name.upper()
        user_model.last_name = user.last_name.upper()
        user_model.email = user.email.lower()
        user_model.mobile = user.mobile
        user_model.password = user.password
        user_model.isAdmin = False
        user_model.address = user.address
        user_model.bloodGroup = user.bloodGroup
        user_model.hospital_id = user.hospital_id
        user_model.isAlive = user.isAlive
        db.add(user_model)
        db.commit()
        return user
    else:
        raise HTTPException(status_code=404, detail="User already found")

@app.post("/authenticateUser")
async def create(email:str, password:str, db:Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.email == email).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")
    if password != user_model.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"message": "Authentication successful", "token": user_model.id, "isAdmin": user_model.isAdmin}

@app.put("/forgotPassword")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    temporary_password = str(randint(100000, 999999))
    user.password = temporary_password
    db.commit()
    return {"message": "Temporary password sent successfully", "temporaryPassword": temporary_password}

@app.put("/changePassword")
async def change_password(email: str, old_password:str, new_password:str, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if old_password != user.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    user.password = new_password
    db.commit()
    return {"message": "Password Changed successfully"}

@app.get("/getOrgans")
async def read(db:Session = Depends(get_db)):
    return db.query(models.Organs).all()

@app.get("/getHospital")
async def read(db:Session = Depends(get_db)):
    return db.query(models.Hospital).all()

@app.get("/previousContributions/{user_id}")
async def read(user_id: int, db: Session = Depends(get_db)):
    userR = aliased(models.Users)
    query = (
    db.query(models.Users, models.Donations, models.Organs, userR)
    .join(models.Donations, models.Donations.donor_id == models.Users.id, isouter=False)
    .join(models.Organs, models.Donations.organ_id == models.Organs.id, isouter=False)
    .join(userR, models.Donations.recipient_id == userR.id, isouter=True)
    .filter(models.Users.id == user_id)
    .all()
    )
    donor_data = []
    for donor, donations, organ, recipient in query:
        donation_status = donations.status
        organ_name = organ.organ_name
        recipient_name = f"{recipient.first_name} {recipient.last_name}" if recipient else None
        donor_data.append({
            "organ_name": organ_name,
            "recipient_name": recipient_name,
            "donation_status": donation_status
        })
    return donor_data

@app.put("/contribute/{user_id}/{organ_id}")
async def read(user_id: int, organ_id: int, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    organ = db.query(models.Organs).filter(models.Organs.id == organ_id).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User ID {user_id} : Does Not Exists"
        )
    if organ is None:
        raise HTTPException(
            status_code=404,
            detail=f"Organ ID {organ_id} : Does Not Exists"
        )
    donation_model = models.Donations()
    donation_model.donor_id = user_id
    donation_model.organ_id = organ_id
    db.add(donation_model)
    db.commit()
    return {"message": "Contribution Placed successfully"}

@app.get("/previousRequests/{user_id}")
async def read(user_id: int, db: Session = Depends(get_db)):
    userR = aliased(models.Users)
    query = (
    db.query(models.Users, models.Donations, models.Organs, userR)
    .join(models.Donations, models.Donations.recipient_id == models.Users.id, isouter=False)
    .join(models.Organs, models.Donations.organ_id == models.Organs.id, isouter=False)
    .join(userR, models.Donations.donor_id == userR.id, isouter=True)
    .filter(models.Users.id == user_id)
    .all()
    )
    donor_data = []
    for recipient, donations, organ, donor in query:
        donation_status = donations.status
        organ_name = organ.organ_name
        donor_name = f"{donor.first_name} {donor.last_name}" if donor else None
        donor_data.append({
            "organ_name": organ_name,
            "recipient_name": donor_name,
            "donation_status": donation_status
        })
    return donor_data

@app.put("/request/{user_id}/{organ_id}")
async def read(user_id: int, organ_id: int, reason: str, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    organ = db.query(models.Organs).filter(models.Organs.id == organ_id).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User ID {user_id} : Does Not Exists"
        )
    if organ is None:
        raise HTTPException(
            status_code=404,
            detail=f"Organ ID {organ_id} : Does Not Exists"
        )
    donation_model = models.Donations()
    donation_model.recipient_id = user_id
    donation_model.organ_id = organ_id
    donation_model.reason = reason
    db.add(donation_model)
    db.commit()
    return {"message": "Request Placed successfully"}

# @app.post("/donateOrgan")
# async def create(donation: Donations,user_id: int,db:Session = Depends(get_db)):
#     user = db.query(models.Users).filter(models.Users.id == user_id).first()
#     if user.isDonor:
#         donor_model = models.Donations()
#         donor_model.donor_id = donation.donor_id
#         donor_model.recipient_id = donation.recipient_id
#         donor_model.organ_id = donation.organ_id
#         donor_model.status = donation.status
#         db.add(donor_model)
#         db.commit()
#         return donation
    
# @app.post("/receiveOrgan")
# async def create(receive: Donations,user_id: int,db:Session = Depends(get_db)):
#     user = db.query(models.Users).filter(models.Users.id == user_id).first()
#     if user.isRecipient:
#         receipent_model = models.Donations()
#         receipent_model.donor_id = receive.donor_id
#         receipent_model.recipient_id = receive.recipient_id
#         receipent_model.organ_id = receive.organ_id
#         receipent_model.status = receive.status
#         db.add(receipent_model)
#         db.commit()
#         return receive

# @app.get("/getDonor")
# async def read(db:Session = Depends(get_db)):
#     query = (
#         db.query(models.Users, models.Organs, models.Hospitals)
#         .join(models.Organs, models.Users.organ_id == models.Organs.id, isouter=True)
#         .join(models.Hospitals, models.Users.hospital_id == models.Hospitals.id, isouter=True)
#         .filter(models.Users.isDonor == True)
#         .all()
#     )
#     donor_data = []
#     for user, organ, hospital in query:
#         donor_data.append({
#             "user_id": user.id,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "email": user.email,
#             "mobile": user.mobile,
#             "address": user.address,
#             "bloodGroup": user.bloodGroup,
#             "organ_name": organ.organ_name if organ else None,
#             "hospital_name": hospital.hospital_name if hospital else None,
#             "isAlive": user.isAlive,
#             "isDonor": user.isDonor,
#             "isRecipient": user.isRecipient,
#         })
#     return donor_data

# @app.get("/getRecipient")
# async def read(db:Session = Depends(get_db)):
#     recepient = db.query(models.Users).filter(models.Users.isRecipient == True).all()
#     return recepient

# @app.put("/registerDR/{user_id}")
# async def create(user_id:int, user: Users, db:Session = Depends(get_db)):
#     user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
#     if user_model is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"ID {user_id} : Does Not Exists"
#         )
#     user_model.address = user.address
#     user_model.bloodGroup = user.bloodGroup
#     user_model.organ_id = user.organ_id
#     user_model.hospital_id = user.hospital_id
#     user_model.isAlive = user.isAlive
#     user_model.isDonor = user.isDonor
#     user_model.isRecipient = user.isRecipient
#     db.add(user_model)
#     db.commit()
#     return user

# @app.put("/delete/{book_id}")
# async def delete(book_id: int, db:Session = Depends(get_db)):
#     book_model = db.query(models.Books).filter(models.Books.id == book_id).first()
#     if book_model is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"ID {book_id} : Does Not Exists"
#         )
#     db.query(models.Books).filter(models.Books.id == book_id).delete()
#     db.commit()