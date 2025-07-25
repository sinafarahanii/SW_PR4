import json
import sys
import logging
from db import init_db, db_session
from flask import Flask, redirect, request, jsonify
from flasgger import Swagger
from models import Subscription, Receipt
import stripe
from sqlalchemy.exc import SQLAlchemyError

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="APP %(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log"),
    ]
)
logger = logging.getLogger(__name__)

# --- Initialize DB ---
try:
    init_db()
    logger.info("Database initialized.")
except Exception as e:
    logger.exception("Database initialization failed.")
    sys.exit(1)

# --- Stripe Setup ---
stripe.api_key = 'sk_test_51P80mw055qYUKJJtHpafkOLq4zks7y3q5dDJ8LX4UqfXsCie8TWfhwRXAyCDWZQjh3Hf3Lnv9rX6VWNPQy8Ll3Db00rD7OHVJb'

app = Flask(__name__, static_url_path='', static_folder='public')
swagger = Swagger(app)
YOUR_DOMAIN = 'http://localhost:4242'

# --- Routes ---

@app.route('/create-checkout-session/', methods=['POST'])
def create_checkout_session():
    try:
        logger.info("Creating Stripe checkout session.")
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': 'price_1P88Qu055qYUKJJtyciVQrAk',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cancel.html?session_id={CHECKOUT_SESSION_ID}',
        )
        logger.info(f"Checkout session created: {checkout_session.id}")
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logger.exception("Failed to create checkout session.")
        return jsonify({'error': str(e)}), 500


@app.route('/checkout-session/<session_id>', methods=['GET'])
def get_checkout_session(session_id):
    try:
        logger.info(f"Retrieving Stripe session {session_id}")
        session = stripe.checkout.Session.retrieve(session_id, expand=['customer_details'])

        existing = db_session.query(Receipt).filter_by(session_id=session.id).first()
        if not existing:
            logger.info(f"Saving new receipt for session {session.id}")
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
            logger.info("Receipt saved.")
        else:
            logger.info(f"Receipt for session {session.id} already exists.")

        return jsonify({
            'id': session.id,
            'payment_status': session.payment_status,
            'status': session.status,
            'amount_total': session.amount_total,
            'currency': session.currency,
            'email': session.customer_details.email if session.customer_details else None
        })
    except stripe.error.StripeError as e:
        logger.exception("Stripe error occurred.")
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        logger.exception("Database error while saving receipt.")
        db_session.rollback()
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return jsonify({'error': str(e)}), 500


@app.route('/api/payments', methods=['GET'])
def list_payments():
    try:
        logger.info("Fetching all receipts from database.")
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
    except SQLAlchemyError as e:
        logger.exception("Failed to fetch receipts from the database.")
        return jsonify({'error': 'Database error'}), 500


@app.route('/api/payments/<int:receipt_id>', methods=['PATCH'])
def update_payment_status(receipt_id):
    try:
        logger.info(f"Updating payment status for receipt {receipt_id}")
        data = request.json
        receipt = db_session.query(Receipt).get(receipt_id)
        if not receipt:
            logger.warning(f"Receipt {receipt_id} not found.")
            return jsonify({'error': 'Receipt not found'}), 404

        receipt.payment_status = data.get('payment_status', receipt.payment_status)
        db_session.commit()
        logger.info(f"Payment status for receipt {receipt_id} updated to {receipt.payment_status}")
        return jsonify({'message': 'Updated'})
    except SQLAlchemyError as e:
        logger.exception("Failed to update receipt in database.")
        db_session.rollback()
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.exception("Unexpected error while updating payment status.")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    try:
        logger.info("Starting Flask app on port 4242")
        app.run(port=4242)
    except Exception as e:
        logger.exception("Flask app failed to start.")
        sys.exit(1)
