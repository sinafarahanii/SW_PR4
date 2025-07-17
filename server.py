#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import json
from db import init_db, db_session
from flask import Flask, redirect, request, jsonify
from models import Subscription
import stripe


init_db()
# This is your test secret API key.
stripe.api_key = 'sk_test_51P80mw055qYUKJJtHpafkOLq4zks7y3q5dDJ8LX4UqfXsCie8TWfhwRXAyCDWZQjh3Hf3Lnv9rX6VWNPQy8Ll3Db00rD7OHVJb'

app = Flask(__name__,
            static_url_path='',
            static_folder='public')

YOUR_DOMAIN = 'http://localhost:4242'


@app.route('/create-checkout-session/', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': 'price_1P88Qu055qYUKJJtyciVQrAk',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)


@app.route('/webhook', methods=['POST'])
def webhook():
    resp_dict = json.loads(request.data.decode('utf-8'))
    if resp_dict['data']['object']['object'] != 'subscription':
        return jsonify({'status': 'success'})
    id = resp_dict['data']['object']['id']
    print(id)
    record = Subscription(id=id)
    try:
        db_session.add(record)
        db_session.commit()
    except Exception as e:
        pass
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(port=4242)

