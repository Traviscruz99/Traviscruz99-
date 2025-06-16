import requests
import json
import time
import random
import string
import os
from datetime import datetime

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"
print(f"Testing API at: {API_URL}")

# Test data
test_user = {
    "email": f"test.user.{int(time.time())}@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+90 555 123 4567"
}

# Store session data
session = {
    "token": None,
    "user_id": None,
    "accounts": [],
    "cards": []
}

def print_test_header(test_name):
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_register():
    print_test_header("User Registration")
    
    url = f"{API_URL}/auth/register"
    response = requests.post(url, json=test_user)
    print_response(response)
    
    assert response.status_code == 200, f"Registration failed with status {response.status_code}"
    data = response.json()
    assert "token" in data, "Token not found in registration response"
    assert "user" in data, "User data not found in registration response"
    
    session["token"] = data["token"]
    session["user_id"] = data["user"]["id"]
    
    print("✅ Registration successful")
    return True

def test_login():
    print_test_header("User Login")
    
    url = f"{API_URL}/auth/login"
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(url, json=login_data)
    print_response(response)
    
    assert response.status_code == 200, f"Login failed with status {response.status_code}"
    data = response.json()
    assert "token" in data, "Token not found in login response"
    
    session["token"] = data["token"]
    
    print("✅ Login successful")
    return True

def test_get_dashboard():
    print_test_header("Get Dashboard")
    
    url = f"{API_URL}/dashboard"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Dashboard retrieval failed with status {response.status_code}"
    data = response.json()
    
    assert "user" in data, "User data not found in dashboard"
    assert "accounts" in data, "Accounts not found in dashboard"
    assert "total_balance" in data, "Total balance not found in dashboard"
    
    # Check if default account was created with ₺1000
    assert len(data["accounts"]) > 0, "No accounts found in dashboard"
    default_account = data["accounts"][0]
    assert default_account["balance"] == 1000.0, f"Default account should have ₺1000, found {default_account['balance']}"
    
    # Store account info for later tests
    session["accounts"] = data["accounts"]
    
    print("✅ Dashboard retrieval successful")
    return True

def test_get_accounts():
    print_test_header("Get Accounts")
    
    url = f"{API_URL}/accounts"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Account retrieval failed with status {response.status_code}"
    accounts = response.json()
    
    assert len(accounts) > 0, "No accounts found"
    assert accounts[0]["account_type"] == "checking", "Default account should be checking type"
    assert accounts[0]["balance"] == 1000.0, f"Default account should have ₺1000, found {accounts[0]['balance']}"
    
    # Update session accounts
    session["accounts"] = accounts
    
    print("✅ Account retrieval successful")
    return True

def test_create_accounts():
    print_test_header("Create Additional Accounts")
    
    url = f"{API_URL}/accounts"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    # Create savings account
    savings_data = {"account_type": "savings", "currency": "TRY"}
    savings_response = requests.post(url, json=savings_data, headers=headers)
    print("Savings Account Response:")
    print_response(savings_response)
    
    assert savings_response.status_code == 200, f"Savings account creation failed with status {savings_response.status_code}"
    savings_account = savings_response.json()
    assert savings_account["account_type"] == "savings", "Created account should be savings type"
    
    # Create investment account
    investment_data = {"account_type": "investment", "currency": "TRY"}
    investment_response = requests.post(url, json=investment_data, headers=headers)
    print("Investment Account Response:")
    print_response(investment_response)
    
    assert investment_response.status_code == 200, f"Investment account creation failed with status {investment_response.status_code}"
    investment_account = investment_response.json()
    assert investment_account["account_type"] == "investment", "Created account should be investment type"
    
    # Update accounts in session
    session["accounts"].append(savings_account)
    session["accounts"].append(investment_account)
    
    print("✅ Additional accounts created successfully")
    return True

def test_account_balance():
    print_test_header("Check Account Balance")
    
    if not session["accounts"]:
        print("❌ No accounts available to check balance")
        return False
    
    account_id = session["accounts"][0]["id"]
    url = f"{API_URL}/accounts/{account_id}/balance"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Balance check failed with status {response.status_code}"
    balance_data = response.json()
    
    assert "balance" in balance_data, "Balance not found in response"
    assert "currency" in balance_data, "Currency not found in response"
    assert balance_data["currency"] == "TRY", "Currency should be TRY"
    
    print("✅ Account balance check successful")
    return True

def test_deposit():
    print_test_header("Deposit Money")
    
    if not session["accounts"]:
        print("❌ No accounts available for deposit")
        return False
    
    account_id = session["accounts"][0]["id"]
    deposit_amount = 500.0
    
    url = f"{API_URL}/accounts/{account_id}/deposit"
    headers = {"Authorization": f"Bearer {session['token']}"}
    params = {"amount": deposit_amount}
    
    response = requests.post(url, headers=headers, params=params)
    print_response(response)
    
    assert response.status_code == 200, f"Deposit failed with status {response.status_code}"
    deposit_data = response.json()
    
    assert "message" in deposit_data, "Message not found in deposit response"
    assert "new_balance" in deposit_data, "New balance not found in deposit response"
    assert deposit_data["new_balance"] == 1500.0, f"Expected balance of 1500.0, got {deposit_data['new_balance']}"
    
    print("✅ Deposit successful")
    return True

def test_transfer():
    print_test_header("Transfer Money Between Accounts")
    
    if len(session["accounts"]) < 2:
        print("❌ Need at least 2 accounts for transfer test")
        return False
    
    from_account_id = session["accounts"][0]["id"]
    to_iban = session["accounts"][1]["iban"]
    transfer_amount = 200.0
    
    url = f"{API_URL}/accounts/{from_account_id}/transfer"
    headers = {"Authorization": f"Bearer {session['token']}"}
    transfer_data = {
        "to_iban": to_iban,
        "amount": transfer_amount,
        "description": "Test transfer between accounts"
    }
    
    response = requests.post(url, json=transfer_data, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Transfer failed with status {response.status_code}"
    result = response.json()
    
    assert "message" in result, "Message not found in transfer response"
    assert "transaction_id" in result, "Transaction ID not found in transfer response"
    assert "status" in result, "Status not found in transfer response"
    assert result["status"] == "completed", f"Expected status 'completed', got {result['status']}"
    
    print("✅ Transfer successful")
    return True

def test_bill_payment():
    print_test_header("Bill Payment")
    
    if not session["accounts"]:
        print("❌ No accounts available for bill payment")
        return False
    
    account_id = session["accounts"][0]["id"]
    
    url = f"{API_URL}/accounts/{account_id}/pay-bill"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    bill_data = {
        "bill_type": "electricity",
        "provider": "Türkiye Elektrik Kurumu",
        "account_number": "EL" + ''.join(random.choices(string.digits, k=8)),
        "amount": 75.50
    }
    
    response = requests.post(url, json=bill_data, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Bill payment failed with status {response.status_code}"
    result = response.json()
    
    assert "message" in result, "Message not found in bill payment response"
    assert "transaction_id" in result, "Transaction ID not found in bill payment response"
    assert "new_balance" in result, "New balance not found in bill payment response"
    
    print("✅ Bill payment successful")
    return True

def test_get_transactions():
    print_test_header("Get Transaction History")
    
    if not session["accounts"]:
        print("❌ No accounts available to check transactions")
        return False
    
    account_id = session["accounts"][0]["id"]
    url = f"{API_URL}/accounts/{account_id}/transactions"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Transaction history retrieval failed with status {response.status_code}"
    transactions = response.json()
    
    assert isinstance(transactions, list), "Transactions should be a list"
    assert len(transactions) > 0, "No transactions found"
    
    # Verify transaction fields
    for transaction in transactions:
        assert "id" in transaction, "Transaction ID missing"
        assert "amount" in transaction, "Transaction amount missing"
        assert "transaction_type" in transaction, "Transaction type missing"
        assert "status" in transaction, "Transaction status missing"
    
    print("✅ Transaction history retrieval successful")
    return True

def test_create_card():
    print_test_header("Create Virtual Card")
    
    if not session["accounts"]:
        print("❌ No accounts available for card creation")
        return False
    
    account_id = session["accounts"][0]["id"]
    url = f"{API_URL}/cards"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    card_data = {
        "account_id": account_id,
        "card_type": "debit",
        "limit": None
    }
    
    response = requests.post(url, json=card_data, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Card creation failed with status {response.status_code}"
    card = response.json()
    
    assert "id" in card, "Card ID missing"
    assert "card_number" in card, "Card number missing"
    assert "card_type" in card, "Card type missing"
    assert "status" in card, "Card status missing"
    assert card["status"] == "active", f"Expected card status 'active', got {card['status']}"
    
    session["cards"].append(card)
    
    print("✅ Card creation successful")
    return True

def test_get_cards():
    print_test_header("Get Cards")
    
    url = f"{API_URL}/cards"
    headers = {"Authorization": f"Bearer {session['token']}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    
    assert response.status_code == 200, f"Card retrieval failed with status {response.status_code}"
    cards = response.json()
    
    assert isinstance(cards, list), "Cards should be a list"
    assert len(cards) > 0, "No cards found"
    
    # Verify card fields
    for card in cards:
        assert "id" in card, "Card ID missing"
        assert "card_number" in card, "Card number missing"
        assert "card_type" in card, "Card type missing"
        assert "status" in card, "Card status missing"
    
    print("✅ Card retrieval successful")
    return True

def run_all_tests():
    tests = [
        ("User Registration", test_register),
        ("User Login", test_login),
        ("Dashboard Retrieval", test_get_dashboard),
        ("Account Retrieval", test_get_accounts),
        ("Create Additional Accounts", test_create_accounts),
        ("Account Balance Check", test_account_balance),
        ("Money Deposit", test_deposit),
        ("Money Transfer", test_transfer),
        ("Bill Payment", test_bill_payment),
        ("Transaction History", test_get_transactions),
        ("Create Virtual Card", test_create_card),
        ("Card Retrieval", test_get_cards)
    ]
    
    results = {}
    all_passed = True
    
    print("\n" + "="*80)
    print(f"STARTING BACKEND API TESTS AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    print("="*80 + "\n")
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with error: {str(e)}")
            results[test_name] = False
            all_passed = False
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
    else:
        print("❌ SOME TESTS FAILED. See details above.")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()