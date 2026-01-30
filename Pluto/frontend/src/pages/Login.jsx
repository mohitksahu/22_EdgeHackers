import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GradientText from '../components/GradientText';
import "../styles/components/Login.css";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Implement actual login logic
  };

  const handleGoogleLogin = () => {
    // TODO: Implement Google OAuth
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <h1>
            <GradientText>PLUTO<span>.</span></GradientText>
          </h1>
          <p className="login-tagline">Truth needs evidence</p>
        </div>

        {/* Email Login */}
        <form className="login-form" onSubmit={handleSubmit}>
          <label>Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button type="submit" className="login-btn">
            Sign in
          </button>
        </form>

        {/* Sign Up Button */}
        <button type="button" className="signup-btn" onClick={() => navigate('/signup')}>
          Create Account
        </button>

        {/* Divider */}
        <div className="divider">
          <span>or continue with</span>
        </div>

        {/* OAuth Buttons */}
        <div className="oauth-section">
          <button className="oauth-btn google" type="button" onClick={handleGoogleLogin}>
            Continue with Google
          </button>
        </div>
      </div>
    </div>
  );
}
