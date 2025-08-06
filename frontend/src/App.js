import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      // Verify token and get user info
      fetch(`${API}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data.detail) {
          // Invalid token
          localStorage.removeItem('token');
          setToken(null);
        } else {
          setUser(data);
        }
      })
      .catch(() => {
        localStorage.removeItem('token');
        setToken(null);
      });
    }
  }, [token]);

  const login = async (username, password) => {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    
    if (res.ok) {
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      return { success: true };
    } else {
      return { success: false, error: data.detail };
    }
  };

  const register = async (username, password, email = '') => {
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, email })
    });
    const data = await res.json();
    
    if (res.ok) {
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      return { success: true };
    } else {
      return { success: false, error: data.detail };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// Rich Text Editor Component
const RichTextEditor = ({ value, onChange, placeholder = "Write your story..." }) => {
  const editorRef = React.useRef(null);

  const formatText = (command, value = null) => {
    document.execCommand(command, false, value);
    onChange(editorRef.current.innerHTML);
  };

  const handleInput = () => {
    onChange(editorRef.current.innerHTML);
  };

  React.useEffect(() => {
    if (editorRef.current && value !== editorRef.current.innerHTML) {
      editorRef.current.innerHTML = value;
    }
  }, [value]);

  return (
    <div className="border border-gray-300 rounded-lg">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-1 p-2 border-b border-gray-200 bg-gray-50">
        <button
          type="button"
          onClick={() => formatText('bold')}
          className="px-3 py-1 text-sm font-bold border rounded hover:bg-gray-200"
        >
          B
        </button>
        <button
          type="button"
          onClick={() => formatText('italic')}
          className="px-3 py-1 text-sm italic border rounded hover:bg-gray-200"
        >
          I
        </button>
        <button
          type="button"
          onClick={() => formatText('underline')}
          className="px-3 py-1 text-sm underline border rounded hover:bg-gray-200"
        >
          U
        </button>
        <div className="w-px h-6 bg-gray-300 mx-1"></div>
        <button
          type="button"
          onClick={() => formatText('formatBlock', 'h1')}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-200"
        >
          H1
        </button>
        <button
          type="button"
          onClick={() => formatText('formatBlock', 'h2')}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-200"
        >
          H2
        </button>
        <button
          type="button"
          onClick={() => formatText('formatBlock', 'p')}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-200"
        >
          P
        </button>
        <div className="w-px h-6 bg-gray-300 mx-1"></div>
        <button
          type="button"
          onClick={() => formatText('insertUnorderedList')}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-200"
        >
          • List
        </button>
        <button
          type="button"
          onClick={() => formatText('insertOrderedList')}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-200"
        >
          1. List
        </button>
      </div>
      
      {/* Editor */}
      <div
        ref={editorRef}
        contentEditable
        onInput={handleInput}
        className="min-h-[300px] p-4 outline-none"
        style={{ 
          wordWrap: 'break-word',
          lineHeight: '1.6'
        }}
        data-placeholder={placeholder}
      />
      
      <style jsx>{`
        [contenteditable]:empty::before {
          content: attr(data-placeholder);
          color: #9ca3af;
        }
      `}</style>
    </div>
  );
};

// Components
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin 
      ? await login(username, password)
      : await register(username, password, email);

    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {isLogin ? 'Sign in to your account' : 'Create new account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Write and share your stories
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            
            {!isLogin && (
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email (optional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            )}
            
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-600 hover:text-blue-500"
            >
              {isLogin ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
            </button>
          </div>
        </form>
        
        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900">Admin Login:</h3>
          <p className="text-sm text-blue-800">Username: <strong>admin</strong></p>
          <p className="text-sm text-blue-800">Password: <strong>admin123</strong></p>
        </div>
      </div>
    </div>
  );
};

const WriteStory = ({ onStoryCreated }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      setError('Please fill in both title and content');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API}/stories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title, content })
      });

      if (res.ok) {
        setTitle('');
        setContent('');
        onStoryCreated();
        alert('Story submitted for review!');
      } else {
        const data = await res.json();
        setError(data.detail || 'Failed to submit story');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Write New Story</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Story Title"
          className="w-full px-4 py-2 text-xl border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        
        <RichTextEditor
          value={content}
          onChange={setContent}
          placeholder="Write your story here..."
        />
        
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Submitting...' : 'Submit Story'}
        </button>
      </form>
    </div>
  );
};

const PublicStories = () => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, token } = useAuth();

  const fetchStories = async () => {
    try {
      const res = await fetch(`${API}/stories/public`);
      const data = await res.json();
      setStories(data);
    } catch (err) {
      console.error('Failed to fetch stories:', err);
    }
    setLoading(false);
  };

  const handleLike = async (storyId) => {
    if (!user) return;
    
    try {
      const res = await fetch(`${API}/stories/${storyId}/like`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      // Update the story in the list
      setStories(stories.map(story => 
        story.id === storyId 
          ? { ...story, likes: data.likes, liked_by: story.liked_by || [] }
          : story
      ));
    } catch (err) {
      console.error('Failed to like story:', err);
    }
  };

  useEffect(() => {
    fetchStories();
  }, []);

  if (loading) return <div className="p-6">Loading stories...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Published Stories</h2>
      
      {stories.length === 0 ? (
        <p className="text-gray-600">No published stories yet.</p>
      ) : (
        <div className="space-y-8">
          {stories.map(story => (
            <div key={story.id} className="bg-white border rounded-lg p-6 shadow-sm">
              <h3 className="text-xl font-bold mb-2">{story.title}</h3>
              <p className="text-sm text-gray-600 mb-4">
                By {story.author_username} • {new Date(story.approved_at).toLocaleDateString()}
              </p>
              
              <div 
                className="prose max-w-none mb-4"
                dangerouslySetInnerHTML={{ __html: story.content }}
              />
              
              <div className="flex items-center justify-between">
                <button
                  onClick={() => handleLike(story.id)}
                  disabled={!user}
                  className={`flex items-center space-x-2 px-3 py-1 rounded-md transition-colors ${
                    user && story.liked_by?.includes(user.id)
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  } disabled:opacity-50`}
                >
                  <span>❤️</span>
                  <span>{story.likes}</span>
                </button>
                
                {!user && (
                  <span className="text-sm text-gray-500">Login to like stories</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const MyStories = () => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  const fetchMyStories = async () => {
    try {
      const res = await fetch(`${API}/stories/my`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setStories(data);
    } catch (err) {
      console.error('Failed to fetch my stories:', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchMyStories();
  }, []);

  if (loading) return <div className="p-6">Loading your stories...</div>;

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${colors[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">My Stories</h2>
      
      {stories.length === 0 ? (
        <p className="text-gray-600">You haven't written any stories yet.</p>
      ) : (
        <div className="space-y-4">
          {stories.map(story => (
            <div key={story.id} className="bg-white border rounded-lg p-4 shadow-sm">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold">{story.title}</h3>
                {getStatusBadge(story.status)}
              </div>
              
              <p className="text-sm text-gray-600 mb-2">
                Created: {new Date(story.created_at).toLocaleDateString()}
                {story.approved_at && (
                  <span> • Approved: {new Date(story.approved_at).toLocaleDateString()}</span>
                )}
              </p>
              
              {story.status === 'approved' && (
                <p className="text-sm text-green-600">❤️ {story.likes} likes</p>
              )}
              
              <div 
                className="mt-3 prose prose-sm max-w-none line-clamp-3"
                dangerouslySetInnerHTML={{ __html: story.content }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const AdminPanel = () => {
  const [pendingStories, setPendingStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  const fetchPendingStories = async () => {
    try {
      const res = await fetch(`${API}/stories/pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setPendingStories(data);
    } catch (err) {
      console.error('Failed to fetch pending stories:', err);
    }
    setLoading(false);
  };

  const moderateStory = async (storyId, status) => {
    try {
      const res = await fetch(`${API}/stories/${storyId}/moderate`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status })
      });
      
      if (res.ok) {
        setPendingStories(pendingStories.filter(story => story.id !== storyId));
      }
    } catch (err) {
      console.error('Failed to moderate story:', err);
    }
  };

  useEffect(() => {
    fetchPendingStories();
  }, []);

  if (loading) return <div className="p-6">Loading pending stories...</div>;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Admin Panel - Story Moderation</h2>
      
      {pendingStories.length === 0 ? (
        <p className="text-gray-600">No stories pending review.</p>
      ) : (
        <div className="space-y-6">
          {pendingStories.map(story => (
            <div key={story.id} className="bg-white border rounded-lg p-6 shadow-sm">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold">{story.title}</h3>
                  <p className="text-sm text-gray-600">
                    By {story.author_username} • {new Date(story.created_at).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => moderateStory(story.id, 'approved')}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => moderateStory(story.id, 'rejected')}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    Reject
                  </button>
                </div>
              </div>
              
              <div 
                className="prose max-w-none"
                dangerouslySetInnerHTML={{ __html: story.content }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const Header = ({ activeTab, setActiveTab }) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-6xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Story Platform</h1>
          
          {user && (
            <div className="flex items-center space-x-6">
              <nav className="flex space-x-4">
                <button
                  onClick={() => setActiveTab('public')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === 'public'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Browse Stories
                </button>
                
                <button
                  onClick={() => setActiveTab('write')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === 'write'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  Write Story
                </button>
                
                <button
                  onClick={() => setActiveTab('my')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === 'my'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  My Stories
                </button>
                
                {user.is_admin && (
                  <button
                    onClick={() => setActiveTab('admin')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      activeTab === 'admin'
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:text-gray-900'
                    }`}
                  >
                    Admin Panel
                  </button>
                )}
              </nav>
              
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-700">
                  {user.username} {user.is_admin && '(Admin)'}
                </span>
                <button
                  onClick={logout}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const App = () => {
  const [activeTab, setActiveTab] = useState('public');
  const { user } = useAuth();

  const handleStoryCreated = () => {
    setActiveTab('my');
  };

  if (!user) {
    return <LoginForm />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main>
        {activeTab === 'public' && <PublicStories />}
        {activeTab === 'write' && <WriteStory onStoryCreated={handleStoryCreated} />}
        {activeTab === 'my' && <MyStories />}
        {activeTab === 'admin' && user.is_admin && <AdminPanel />}
      </main>
    </div>
  );
};

const AppWithAuth = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default AppWithAuth;