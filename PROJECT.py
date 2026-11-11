from fastapi import FastAPI,HTTPException,Header
from pydantic import BaseModel,Field
import json,os

app=FastAPI(title="FASTAPI",summary="Online Product Ordering API")

initial_products=[
    {"id":1,"name":"Macbook","stock":10,"seller_id":1,"price":200000,"ratings":[],"category":"Laptop"},
    {"id":2,"name":"AirPods","stock":10,"seller_id":2,"price":20000,"ratings":[],"category":"Headphones"},
    {"id":3,"name":"OnePlus Smartphone","stock":10,"seller_id":1,"price":45000,"ratings":[],"category":"Phone"}

]


initial_customers=[
    {"id":1,"name":"akhil","email":"akhil@gmail.com","total":0,"canceled":[],"orders":[],"reviewed":[],"amount spent":0},
    {"id":2,"name":"rohan","email":"rohan@gmail.com","total":0,"canceled":[],"orders":[],"reviewed":[],"amount spent":0}
    
]


initial_sellers=[
    {"id":1,"name":"rahul","email":"rahul@gmail.com"},
    {"id":2,"name":"rohit","email":"rohit@gmail.com"}
]


BASE_FOLDER=os.path.dirname(os.path.abspath(__file__))
CUSTOMER_FILE=os.path.join(BASE_FOLDER,"customers.json")
SELLER_FILE=os.path.join(BASE_FOLDER,"sellers.json")
PRODUCT_FILE=os.path.join(BASE_FOLDER,"products.json")


def save_data(path,data):
    with open(path,"w",encoding="utf-8")as file:
        json.dump(data,file,indent=2)

def load_data(path,starting):
    if not os.path.exists(path):
        starting_list=[]
        for prod in starting:
            starting_list.append(prod)
        save_data(path,starting_list)
        return starting_list
    with open(path,"r",encoding="utf-8") as file:
        return json.load(file)

products=load_data(PRODUCT_FILE,initial_products)
customers=load_data(CUSTOMER_FILE,initial_customers)
sellers=load_data(SELLER_FILE,initial_sellers)

class ProductIn(BaseModel):
    id :int
    name :str=Field(min_length=1,max_length=100,examples=["Scooter"])
    seller_id :int
    stock :int=Field(ge=1,le=1000,examples=[25])
    price :int
    category :str=Field(min_length=3,max_length=100)



class Seller(BaseModel):
    name :str=Field(min_length=1,max_length=100,examples=["Neha"])
    email :str=Field(min_length=11,max_length=100,examples=["Neha@gmail.com"])



class Order(BaseModel):
    id :int
    name :str=Field(min_length=1,max_length=100,examples=["Scooter"])
    customer_id :int
    amount :int =Field(min=1,max=1000000,examples=[10000])

class Review(BaseModel):
    id :int
    name :str=Field(min_length=1,max_length=100,examples=["Scooter"])
    customer_id :int
    rating :int=Field(ge=1,le=5,examples=[4])


class Purchase(BaseModel):
        id :int
        name :str=Field(min_length=1,max_length=100,examples=["Scooter"])
        customer_id :int
        stock :int=Field(ge=1,le=1000,examples=[25])
        price :int=Field(min=1,max=1000000,examples=[10000])

class Cancel(BaseModel):
        id :int
        name :str=Field(min_length=1,max_length=100,examples=["Scooter"])
        customer_id :int
        stock :int=Field(ge=1,le=1000,examples=[25])
        price :int=Field(min=1,max=1000000,examples=[10000])


def next_id(products):
     return max([prod["id"]for prod in products],default=0)+1

def check_role(x_role,allowed):
     if x_role.lower() not in("seller","customer","admin"):
          raise HTTPException(status_code=401,detail="WHO R YOU")
     if x_role.lower()!=allowed:
          raise HTTPException(status_code=403,detail="not allowed to perform this action")
     return True

def find_position(id,products):
     for position in range(len(products)):
          if products[position]["id"]==id:
               return position
     raise HTTPException(status_code=404,detail="product not found")





@app.get("/products")
def get_prod(x_role :str=Header(default=None)):
    return products


@app.post("/products",summary="Add a product",response_model=list[ProductIn],status_code=201)
def add_prod(body :ProductIn ,x_role :str|None=Header(default=None)):
     if(check_role(x_role,"seller")==True):
          prod={"id":next_id(products),"name":body.name,"seller_id":body.seller_id,"stock":body.stock,"price":body.price}
          products.append(prod)

     save_data(PRODUCT_FILE,products)
     return products


@app.delete("/products/{prod_id}",response_model=list[ProductIn],summary="remove product")
def prod_delete(prod_id :int,x_role :str|None=Header(default=None)):
     if(check_role(x_role,"seller")==True):
          products.pop(find_position(prod_id,products))
     save_data(PRODUCT_FILE,products)
     return products

@app.put("/products/",response_model=Purchase,summary="Order a Product")
def order_prod(body :Order,x_role :str|None =Header(default=None)):
     if(check_role(x_role,"customer")==True):
          if(products[find_position(body.id,products)]["stock"]==0):
               raise HTTPException(status_code=409,detail="Out of Stock")
          if(products[find_position(body.id,products)]["stock"]<body.amount):
               raise HTTPException(status_code=409,detail="Not enough Stock")
          
          products[find_position(body.id,products)]["stock"]=products[find_position(body.id,products)]["stock"]-body.amount
          customers[find_position(body.customer_id,customers)]["total"]+=body.amount
          customers[find_position(body.customer_id,customers)]["orders"].append(body.id)
          customers[find_position(body.customer_id,customers)]["amount spent"]+=body.price
          save_data(PRODUCT_FILE,products)
          save_data(CUSTOMER_FILE,customers)
          return products[find_position(body.id,products)]
     
     

@app.put("/products/{prod_id}",summary="Cancel a Product")
def cancel_prod(body :Cancel,x_role :str|None =Header(default=None)):
     if(check_role(x_role,"customer")==True):
           if body.id not in customers[find_position(body.customer_id,customers)]["orders"]:
                raise HTTPException(status_code=409,detail="You cant cancel as you havent ordered this item")
           if body.id in customers[find_position(body.customer_id,customers)]["canceled"]:
                raise HTTPException(status_code=409,detail="Not allowed to cancel twice")
           customers[find_position(body.customer_id,customers)]["canceled"].append(body.id)
     
           products[find_position(body.id,products)]["stock"]=products[find_position(body.id,products)]["stock"]+body.amount
           customers[find_position(body.customer_id,customers)]["total"]-=body.amount
           
           save_data(CUSTOMER_FILE,customers)
           save_data(PRODUCT_FILE,products)
           return customers

#if two endpoints have the same path then in docs u will only see one

@app.post("/product")
def review(body :Review,x_role:str|None=Header(default=None),status_code=201,detail="Give Review"): 
     if check_role(x_role,"customer")==True:
          pos=find_position(body.customer_id,customers);
          if body.id not in customers[pos]["orders"]:
               raise HTTPException(status_code=409,detail="Not allowed to review")
          if body.id in customers[find_position(body.customer_id,customers)]["reviews"]:
               raise HTTPException(status_code=403,detail="Not allowed to review twice")
          customers[find_position(body.customer_id,customers)]["reviews"].append(body.id)
          products[find_position(body.id,products)]["ratings"].append(body.rating)
     save_data(PRODUCT_FILE,products);
     return products[find_position(body.id,products)]


@app.delete("/sellers/{seller_id}",status_code=204,summary="Remove a seller")
def remove_seller(seller_id :int,x_role :str|None=Header(default=None)):
     if(check_role(x_role,"admin")==True):
          pos=find_position(seller_id,sellers)
          sellers.pop(pos)
     save_data(SELLER_FILE,sellers)

@app.post("/sellers",status_code=201,summary="Register new seller")
def add_seller(body :Seller,x_role :str=Header(default=None)):
     if(check_role(x_role,"admin")==True):
          seller={"id":next_id(sellers),"name":body.name,"email":body.email}
          sellers.append(seller)
     save_data(SELLER_FILE,sellers)
     return sellers


@app.get("/products{price}",summary="Get products with max price filter")
def get_products(price :int):
     result=[]
     for product in products:
          if product["price"]<=price:
               result.append(product)
     if len(result)==0:
          raise HTTPException(status_code=404,detail="No such Product")
     return result


@app.get("/products/{product_type}",summary="Filter by category")
def get(product_type :str):
     result=[]
     for prod in products:
          if prod["category"].lower().strip() in product_type.lower().strip():
               result.append(prod)
     if len(result)==0:
          raise HTTPException(status_code=404,detail="No product of selected category")
     return result

