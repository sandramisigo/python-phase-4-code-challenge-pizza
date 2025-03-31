#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# GET /restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants= Restaurant.query.all()
    response =[restaurant.to_dict(only=("id", "name", "address"))for restaurant in restaurants]
    return jsonify(response), 200

# GET  /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    
    if restaurant:
        response = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [
                {
                    "id": rp.id,  # RestaurantPizza ID
                    "pizza": {
                        "id": rp.pizza.id,
                        "name": rp.pizza.name,
                        "ingredients": rp.pizza.ingredients
                    },
                    "pizza_id": rp.pizza.id,
                    "price": rp.price,
                    "restaurant_id": rp.restaurant.id
                }
                for rp in restaurant.restaurant_pizzas
            ],
        }
        return jsonify(response), 200
    
    return jsonify({"error": "Restaurant not found"}), 404


# DELETE /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant:
        RestaurantPizza.query.filter_by(restaurant_id=id).delete()
        db.session.delete(restaurant)
        db.session.commit()
        return make_response("", 204)
    else:
        return jsonify({"error": "Restaurant not found"}), 404
    
# GET /Pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas=Pizza.query.all()
    response=[pizza.to_dict(only=("id", "name", "ingredients"))for pizza in pizzas]
    return jsonify(response), 200


# POST /restaurant_pizzas 
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    # Validate input data
    if price is None or pizza_id is None or restaurant_id is None:
        return jsonify({"errors": ["validation errors"]}), 400

    if not (1 <= price <= 30):
        return jsonify({"errors": ["validation errors"]}), 400

    # Ensure the referenced pizza and restaurant exist
    pizza = db.session.get(Pizza, pizza_id)
    restaurant = db.session.get(Restaurant, restaurant_id)

    if not pizza or not restaurant:
        return jsonify({"errors": ["validation errors"]}), 400

    # Create new RestaurantPizza instance
    new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)

    try:
        db.session.add(new_restaurant_pizza)
        db.session.commit()

        # Construct response manually to avoid recursion issues
        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": new_restaurant_pizza.pizza_id,
            "restaurant_id": new_restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }

        return jsonify(response_data), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")  # Debugging
        return jsonify({"errors": ["validation errors"]}), 400

if __name__ == "__main__":
    app.run(port=5555, debug=True)
