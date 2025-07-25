import json
from db import init_db, db_session
from flask import Flask, redirect, request, jsonify
from flasgger import Swagger
from models import Subscription, Receipt
import stripe


init_db()
# This is your test secret API key.
stripe.api_key = 'sk_test_51P80mw055qYUKJJtHpafkOLq4zks7y3q5dDJ8LX4UqfXsCie8TWfhwRXAyCDWZQjh3Hf3Lnv9rX6VWNPQy8Ll3Db00rD7OHVJb'

app = Flask(__name__,
            static_url_path='',
            static_folder='public')

swagger = Swagger(app)

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
            success_url=YOUR_DOMAIN + '/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cancel.html?session_id={CHECKOUT_SESSION_ID}',
        )
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)


@app.route('/checkout-session/<session_id>', methods=['GET'])
def get_checkout_session(session_id):
    """
        Get checkout session and save to database
        ---
        parameters:
          - name: session_id
            in: path
            type: string
            required: true
            description: Stripe session ID
        responses:
          200:
            description: Checkout session retrieved
            schema:
              id: Receipt
              properties:
                id:
                  type: string
                payment_status:
                  type: string
                status:
                  type: string
                amount_total:
                  type: integer
                currency:
                  type: string
                email:
                  type: string
        """
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['customer_details']
        )

        # Check if already saved
        existing = db_session.query(Receipt).filter_by(session_id=session.id).first()
        if not existing:
            receipt = Receipt(
                session_id=session.id,
                payment_status=session.payment_status,
                status=session.status,
                amount_total=session.amount_total,
                currency=session.currency,
                email=(session.customer_details.email if session.customer_details else None)
            )
            db_session.add(receipt)
            db_session.commit()

        return jsonify({
    'id': session.id,
    'payment_status': session.payment_status,
    'status': session.status,
    'amount_total': session.amount_total,
    'currency': session.currency,
    'email': session.customer_details.email if session.customer_details else None
})

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 400


@app.route('/api/payments', methods=['GET'])
def list_payments():
    """
    Get all payments
    ---
    responses:
      200:
        description: List of payments
    """
    receipts = db_session.query(Receipt).all()
    return jsonify([{
        'id': r.id,
        'session_id': r.session_id,
        'email': r.email,
        'amount_total': r.amount_total,
        'currency': r.currency,
        'status': r.status,
        'payment_status': r.payment_status,
        'created_at': r.created_at.isoformat()
    } for r in receipts])


@app.route('/api/payments/<int:receipt_id>', methods=['PATCH'])
def update_payment_status(receipt_id):
    """
    Update payment status
    ---
    parameters:
      - name: receipt_id
        in: path
        type: integer
        required: true
      - name: payment status
        in: body
        required: true
        schema:
          properties:
            payment_status:
              type: string
    responses:
      200:
        description: Updated successfully
    """
    data = request.json
    receipt = db_session.query(Receipt).get(receipt_id)
    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    receipt.payment_status = data.get('payment_status', receipt.payment_status)
    db_session.commit()
    return jsonify({'message': 'Updated'})


if __name__ == '__main__':
    app.run(port=4242)

