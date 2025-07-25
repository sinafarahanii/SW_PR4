import pytest
from unittest.mock import patch, MagicMock
from app import app, db_session, Receipt

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_list_payments_empty_db(client):
    # Mock query to return empty list
    with patch('app.db_session.query') as mock_query:
        mock_query.return_value.all.return_value = []
        res = client.get('/api/payments')
        assert res.status_code == 200
        assert res.json == []

def test_update_payment_status_success(client):
    mock_receipt = MagicMock()
    with patch('app.db_session.query') as mock_query:
        mock_query.return_value.get.return_value = mock_receipt

        res = client.patch('/api/payments/1', json={'payment_status': 'refunded'})
        assert res.status_code == 200
        assert res.json == {'message': 'Updated'}
        assert mock_receipt.payment_status == 'refunded'

def test_update_payment_status_not_found(client):
    with patch('app.db_session.query') as mock_query:
        mock_query.return_value.get.return_value = None
        res = client.patch('/api/payments/999', json={'payment_status': 'refunded'})
        assert res.status_code == 404
        assert res.json == {'error': 'Receipt not found'}

@patch('app.stripe.checkout.Session.create')
def test_create_checkout_session(mock_create, client):
    mock_create.return_value = MagicMock(url='http://mocked-url.com')
    res = client.post('/create-checkout-session/')
    assert res.status_code == 303
    assert 'http://mocked-url.com' in res.location

@patch('app.stripe.checkout.Session.retrieve')
@patch('app.db_session')
def test_get_checkout_session_saves_to_db(mock_db, mock_stripe, client):
    mock_session = MagicMock()
    mock_session.id = 'sess_123'
    mock_session.payment_status = 'paid'
    mock_session.status = 'complete'
    mock_session.amount_total = 2000
    mock_session.currency = 'usd'
    mock_session.customer_details.email = 'test@example.com'
    mock_stripe.return_value = mock_session

    # Simulate no existing receipt
    mock_db.query().filter_by().first.return_value = None

    res = client.get('/checkout-session/sess_123')
    assert res.status_code == 200
    assert res.json['id'] == 'sess_123'
