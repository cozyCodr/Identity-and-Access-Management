import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# CORS Headers


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response


# ROUTES
@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    formatted_drinks = [drink.short() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    })


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    formatted_drinks = [drink.long() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    })


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    try:
        drink_name = body.get('title', None)
        drink_recipe = json.dumps(body.get('recipe', None))
        drink = Drink(title=drink_name, recipe=drink_recipe)
        drink.insert()

        drink = drink.long()

        return jsonify({
            'success': True,
            'drinks': drink
        }), 200
    except:
        abort(422)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(jwt, id):
    body = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        abort(404)
    try:
        req_title = body.get('title', None)
        req_recipe = json.dumps(body.get('recipe', None))
        drink.title = req_title
        drink.recipe = req_recipe
        drink.update()
        drinks = []
        drinks.append(drink.long())

        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200
    except:
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)
    if drink:
        drink.delete()

        return jsonify({
            'success': True,
            'delete': id
        }), 200
    else:
        abort(404)


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
    }), 404


@app.errorhandler(AuthError)
def unauthenticated(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error
    })
