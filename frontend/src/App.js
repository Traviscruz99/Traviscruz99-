import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { token: newToken, user: userData } = response.data;
      
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { token: newToken, user: newUser } = response.data;
      
      setToken(newToken);
      setUser(newUser);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let result;
      if (isLogin) {
        result = await login(formData.email, formData.password);
      } else {
        result = await register(formData);
      }

      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-blue-600 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">İşBank Digital</h1>
          <p className="text-gray-600 mt-2">
            {isLogin ? 'Hesabınıza giriş yapın' : 'Yeni hesap oluşturun'}
          </p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ad</label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Soyad</label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">E-posta</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 font-medium"
          >
            {loading ? 'İşlem yapılıyor...' : (isLogin ? 'Giriş Yap' : 'Hesap Oluştur')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            {isLogin ? 'Hesabınız yok mu? Kayıt olun' : 'Zaten hesabınız var mı? Giriş yapın'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [transferData, setTransferData] = useState({
    to_iban: '',
    amount: '',
    description: ''
  });
  const [billData, setBillData] = useState({
    bill_type: 'electricity',
    provider: '',
    account_number: '',
    amount: ''
  });
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeposit = async (accountId) => {
    const amount = prompt('Yatırılacak miktar:');
    if (amount && parseFloat(amount) > 0) {
      try {
        await axios.post(`${API}/accounts/${accountId}/deposit`, null, {
          params: { amount: parseFloat(amount) }
        });
        await fetchDashboardData();
        alert('Para yatırma işlemi başarılı!');
      } catch (error) {
        alert('İşlem başarısız!');
      }
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    if (!dashboardData.accounts.length) return;

    try {
      await axios.post(`${API}/accounts/${dashboardData.accounts[0].id}/transfer`, {
        to_iban: transferData.to_iban,
        amount: parseFloat(transferData.amount),
        description: transferData.description
      });
      await fetchDashboardData();
      setTransferData({ to_iban: '', amount: '', description: '' });
      alert('Transfer başarılı!');
    } catch (error) {
      alert('Transfer başarısız: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
    }
  };

  const handleBillPayment = async (e) => {
    e.preventDefault();
    if (!dashboardData.accounts.length) return;

    try {
      await axios.post(`${API}/accounts/${dashboardData.accounts[0].id}/pay-bill`, {
        bill_type: billData.bill_type,
        provider: billData.provider,
        account_number: billData.account_number,
        amount: parseFloat(billData.amount)
      });
      await fetchDashboardData();
      setBillData({ bill_type: 'electricity', provider: '', account_number: '', amount: '' });
      alert('Fatura ödemesi başarılı!');
    } catch (error) {
      alert('Ödeme başarısız: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">İşBank Digital</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Hoşgeldin, {user?.first_name}</span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Çıkış
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { key: 'overview', label: 'Genel Bakış', icon: '📊' },
              { key: 'accounts', label: 'Hesaplarım', icon: '💳' },
              { key: 'transfer', label: 'Para Transferi', icon: '💸' },
              { key: 'bills', label: 'Fatura Ödemesi', icon: '🧾' },
              { key: 'cards', label: 'Kartlarım', icon: '💳' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Balance Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 text-white">
                  <h3 className="text-sm font-medium opacity-90">Toplam Bakiye</h3>
                  <p className="text-3xl font-bold mt-2">
                    ₺{dashboardData?.total_balance?.toLocaleString('tr-TR', { minimumFractionDigits: 2 }) || '0.00'}
                  </p>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm border">
                  <h3 className="text-sm font-medium text-gray-600">Aktif Hesaplar</h3>
                  <p className="text-3xl font-bold mt-2 text-gray-900">
                    {dashboardData?.accounts?.length || 0}
                  </p>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm border">
                  <h3 className="text-sm font-medium text-gray-600">Bu Ay İşlem</h3>
                  <p className="text-3xl font-bold mt-2 text-gray-900">
                    {dashboardData?.recent_transactions?.length || 0}
                  </p>
                </div>
              </div>

              {/* Recent Transactions */}
              <div className="bg-white rounded-xl shadow-sm border">
                <div className="p-6 border-b">
                  <h3 className="text-lg font-semibold text-gray-900">Son İşlemler</h3>
                </div>
                <div className="divide-y">
                  {dashboardData?.recent_transactions?.slice(0, 5).map((transaction) => (
                    <div key={transaction.id} className="p-6 flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center mr-4">
                          {transaction.transaction_type === 'deposit' ? '⬇️' : 
                           transaction.transaction_type === 'transfer' ? '↔️' : '💳'}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{transaction.description}</p>
                          <p className="text-sm text-gray-600">
                            {new Date(transaction.created_at).toLocaleDateString('tr-TR')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-semibold ${
                          transaction.transaction_type === 'deposit' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {transaction.transaction_type === 'deposit' ? '+' : '-'}
                          ₺{transaction.amount.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                        </p>
                        <p className="text-sm text-gray-600 capitalize">{transaction.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Accounts Tab */}
          {activeTab === 'accounts' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900">Hesaplarım</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {dashboardData?.accounts?.map((account) => (
                  <div key={account.id} className="bg-white rounded-xl shadow-sm border p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-semibold text-gray-900 capitalize">
                          {account.account_type} Hesabı
                        </h3>
                        <p className="text-sm text-gray-600">IBAN: {account.iban}</p>
                      </div>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Aktif
                      </span>
                    </div>
                    <div className="mb-4">
                      <p className="text-2xl font-bold text-gray-900">
                        ₺{account.balance.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                      </p>
                      <p className="text-sm text-gray-600">{account.currency}</p>
                    </div>
                    <button
                      onClick={() => handleDeposit(account.id)}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
                    >
                      Para Yatır
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transfer Tab */}
          {activeTab === 'transfer' && (
            <div className="max-w-md mx-auto">
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Para Transferi</h2>
                <form onSubmit={handleTransfer} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Alıcı IBAN
                    </label>
                    <input
                      type="text"
                      value={transferData.to_iban}
                      onChange={(e) => setTransferData({...transferData, to_iban: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="TR00 0000 0000 0000 0000 0000 00"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Miktar (₺)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={transferData.amount}
                      onChange={(e) => setTransferData({...transferData, amount: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Açıklama
                    </label>
                    <input
                      type="text"
                      value={transferData.description}
                      onChange={(e) => setTransferData({...transferData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Transfer açıklaması"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 font-medium"
                  >
                    Transfer Yap
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Bills Tab */}
          {activeTab === 'bills' && (
            <div className="max-w-md mx-auto">
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Fatura Ödemesi</h2>
                <form onSubmit={handleBillPayment} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fatura Türü
                    </label>
                    <select
                      value={billData.bill_type}
                      onChange={(e) => setBillData({...billData, bill_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="electricity">Elektrik</option>
                      <option value="gas">Doğalgaz</option>
                      <option value="water">Su</option>
                      <option value="telecom">Telefon</option>
                      <option value="internet">İnternet</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Şirket Adı
                    </label>
                    <input
                      type="text"
                      value={billData.provider}
                      onChange={(e) => setBillData({...billData, provider: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Örn: TEDAŞ, Türk Telekom"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Müşteri Numarası
                    </label>
                    <input
                      type="text"
                      value={billData.account_number}
                      onChange={(e) => setBillData({...billData, account_number: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tutar (₺)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={billData.amount}
                      onChange={(e) => setBillData({...billData, amount: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 font-medium"
                  >
                    Fatura Öde
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Cards Tab */}
          {activeTab === 'cards' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900">Kartlarım</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {dashboardData?.cards?.map((card) => (
                  <div key={card.id} className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl p-6 text-white">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="text-sm opacity-75">İşBank</p>
                        <p className="text-lg font-semibold capitalize">{card.card_type}</p>
                      </div>
                      <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full"></div>
                    </div>
                    <div className="mb-4">
                      <p className="text-xl font-mono tracking-wider">{card.card_number}</p>
                    </div>
                    <div className="flex justify-between items-end">
                      <div>
                        <p className="text-xs opacity-75">Geçerlilik</p>
                        <p className="text-sm">
                          {new Date(card.expires_at).toLocaleDateString('tr-TR', { 
                            year: '2-digit', 
                            month: '2-digit' 
                          })}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs opacity-75">Durum</p>
                        <p className="text-sm capitalize">{card.status}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
};

// Main App Component
function App() {
  const { token } = useAuth();

  return (
    <div className="App">
      {token ? <Dashboard /> : <LoginPage />}
    </div>
  );
}

// App with Provider
function AppWithProvider() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithProvider;